"""
Functions for generating simple markov chains for sequences of words. Allows for scoring of
sentences based on completion frequency.
"""
import random
import redis

PREFIX = 'markov'
SEPARATOR=':'
STOP='\x02'

PUNCTUATION = [",", ".", ";", "!","?","(",")"]

class Markov(object):
    """
    Simple wrapper for markov functions
    """
    def __init__(self, prefix=None, key_length=2, completion_length=1, db=0, host='localhost', port=6379, password=None):
        self.client = redis.Redis(db=db, host=host, port=port, password=password)
        self.prefix = prefix or PREFIX
        self.key_length = key_length
        self.completion_length = completion_length

    def add_line_to_index(self, line):
        add_line_to_index(line, self.client, self.key_length, self.completion_length, self.prefix)

    def score_for_line(self, line):
        return score_for_line(line, self.client, self.key_length, self.completion_length, self.prefix)

    def generate(self, seed=None, min_words=2, max_words=1000, count_punctuation=True):
        return generate(self.client, seed=seed, prefix=self.prefix, min_words=min_words, max_words=max_words, key_length=self.key_length, count_punctuation=count_punctuation)
    

def add_line_to_index(line, client, key_length=2, completion_length=1, prefix=PREFIX):
    """
    Add a line to our index of markov chains

    @param line: a list of words
    @param key_length: the desired length for our keys
    @param completion_length: the desired completion length
    """
    key, completion = get_key_and_completion(line, key_length, completion_length, prefix)
    if key and completion:
        completion = make_key(completion)
        client.zincrby(key, completion)       
        add_line_to_index(line[1:], client, key_length, completion_length, prefix)
    else:
        return
        
def make_key(key, prefix=None):
    """
    Construct a Redis-friendly key from the list or tuple provided
    """
    if type(key) not in [str, unicode]:
        key = SEPARATOR.join(key)
        if prefix:
            key = SEPARATOR.join((prefix, key))
    return key

def max_for_key(key, client):
    """
    Get the maximum score for a completion on this key
    """
    maximum = client.zrevrange(key, 0, 0, withscores=True)
    if maximum:
        return maximum[0][1]
    else:
        return 0
    
def min_for_key(key, client):
    """
    Get the minimum score for a completion on this key
    """
    minimum = client.zrange(key, 0, 0, withscores=True)
    if minimum:
        return minimum[0][1]
    else:
        return 0

def score_for_completion(key, completion, client, normalize_to=100):
    """
    Get the normalized score for a completion
    """
    raw_score = client.zscore(key, make_key(completion)) or 0
    maximum = max_for_key(key, client) or 1
    return (raw_score/maximum) * normalize_to

def _score_for_line(line, client, key_length, completion_length, prefix, count=0):
    """
    Recursive function for iterating over all possible key/completion sets in a line
    and scoring them
    """
    score = 0
    key, completion = get_key_and_completion(line, key_length, completion_length, prefix)
    if key and completion:
        score = score_for_completion(key, completion, client)
        new_score, count = _score_for_line(line[1:], client, key_length, completion_length, prefix, count+1)
        score += new_score
    else:
        score = 0
    return score, count

def score_for_line(line, client, key_length=2, completion_length=1, prefix=PREFIX):
    """
    Score a line of text for fit based on our markov model
    """
    score, count = _score_for_line(line, client, key_length, completion_length, prefix)
    if count > 0:
        return score/count
    else:
        return 0

def generate(client, seed=None, prefix=None, min_words=2, max_words=1000, key_length=2, count_punctuation=True):
    """
    Generate some text based on our model
    """
    if seed is None:
        key, seed = get_random_key_and_seed(client,prefix)      
    else:
        key = make_key(seed[-1*key_length:], prefix=prefix)

    completion = get_completion(client, key)
    if completion and STOP not in completion.split(SEPARATOR):
        completion = completion.split(SEPARATOR)
        if count_tokens(seed, count_punctuation) + count_tokens(completion, count_punctuation) < max_words:
            seed += completion
            return generate(client, seed, prefix, min_words, max_words, key_length, count_punctuation)
        elif count_tokens(seed, count_punctuation) + count_tokens(completion, count_punctuation) == max_words:
            return seed + completion          
    
    elif count_tokens(seed, count_punctuation) <= min_words:
        if STOP in seed:
            seed.remove(STOP)
        if count_tokens(seed, count_punctuation) - min_words > key_length:    
            key, new_seed = get_random_key_and_seed(client, prefix)
            seed += new_seed
            return generate(client, seed, prefix, min_words, max_words, key_length, count_punctuation) 
        else:
            return seed
    else:
        try:
            seed.remove(STOP)
        except:
            pass
        return seed

def count_tokens(seed, count_punctuation=True):
    if count_punctuation :
        return len(seed)
    else:
        return len([item for item in seed if item not in PUNCTUATION]) 
     

def get_random_key_and_seed(client, prefix=None):
    key = client.randomkey()

    seed = key.split(SEPARATOR)
    if prefix is not None:
        while prefix not in seed or len([item for item in seed if item in PUNCTUATION]) > 0:
            key = client.randomkey()
            seed = key.split(SEPARATOR)
        seed.remove(prefix)
    return key, seed
    
def get_completion(client, key, exclude_stops=False):
    """
    Get a possible complete for some key
    """
    completion = None
    completions = client.zrevrange(key, 0, -1)
    if len(completions) > 0:
        completion = random.choice(completions)
    return completion


def get_key_and_completion(line, key_length, completion_length, prefix):
    """
    Get a key and completion from the given list of words
    """
    if len(line) >= key_length and STOP not in line[0:key_length]:
        key = make_key(line[0:key_length], prefix=prefix)
        if completion_length > 1:
            completion = line[key_length:key_length+completion_length]
        else:
            try:
                completion = line[key_length]
            except IndexError:
                completion = STOP
        completion = make_key(completion)
        return (key, completion)
    else:
        return (False,False)
