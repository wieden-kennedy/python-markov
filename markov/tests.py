"""
Tests for the markov package
"""
import redis
import unittest
import markov
from markov import Markov, add_line_to_index, make_key, max_for_key, min_for_key,\
     score_for_completion, score_for_line, get_key_and_completion, generate, get_relevant_key_and_seed, \
     get_random_key_and_seed, get_completion, STOP

class TestMarkovFunctions(unittest.TestCase):
    """
    Test our markov chain construction and phrase scoring functions
    """
    def setUp(self):
        """
        Create a redis client and define a prefix space for this test
        """
        self.client = redis.Redis(db=11)
        self.prefix = 'test'

    def test_make_key(self):
        """
        Test that the make_key function behaves as expected
        """
        key = make_key(('foo','bar'),self.prefix)
        self.assertEqual(key, 'test:foo:bar')
        key = make_key(('foo','bar'))
        self.assertEqual(key, 'foo:bar')
        
    def test_score_for_completion(self):
        """
        Test that score_for_completion scores completions according to our model
        """
        self.test_add_line_to_index()
        self.assertEqual(score_for_completion('test:i:ate', 'a', self.client), 100)
        self.assertEqual(score_for_completion('test:i:ate', 'one', self.client), 50)

    def test_max_for_key(self):
        """
        Test that max_for_key correctly finds the frequency of the most common completion
        """
        self.test_add_line_to_index()
        self.assertEqual(max_for_key('test:i:ate', self.client), 2)
        self.assertEqual(max_for_key('test:stupidkey', self.client), 0)

    def test_min_for_key(self):
        """
        Test that min_for_key correctly finds the frequency of the least common completion
        """
        self.test_add_line_to_index()
        self.assertEqual(min_for_key('test:i:ate', self.client), 1)
        self.assertEqual(min_for_key('test:stupidkey', self.client), 0)
        
    def test_add_line_to_index(self):
        """
        Test that adding lines behaves as expected
        """
        line = ['i','ate','a','peach']
        line1 = ['i','ate','one','peach']
        line2 = ['i','ate','a', 'sandwich']

        add_line_to_index(line, self.client, prefix="test")
        self.assertEqual(self.client.zscore("test:i:ate", "a"), 1.0)
        self.assertEqual(self.client.zscore("test:ate:a", "peach"), 1.0)

        add_line_to_index(line1, self.client, prefix="test")
        self.assertEqual(self.client.zscore("test:i:ate", "a"), 1.0)
        self.assertEqual(self.client.zscore("test:ate:a", "peach"), 1.0)
        self.assertEqual(self.client.zscore("test:ate:one", "peach"), 1.0)
        self.assertEqual(self.client.zscore("test:i:ate", "one"), 1.0)

        add_line_to_index(line2, self.client, prefix="test")
        self.assertEqual(self.client.zscore("test:i:ate", "a"), 2)
        self.assertEqual(self.client.zscore("test:ate:a", "sandwich"), 1.0)
        
    def test_score_for_line(self):
        """
        Ensure that score_for_line rates lines according to our model
        """
        self.test_add_line_to_index()
        line = ['i','ate','a','peach']
        line2 = ['i','ate','a', 'pizza']
        line3 = ['i','ate','one','sandwich']
        
        self.assertEqual(score_for_line(line, self.client, prefix=self.prefix), 100)
        self.assertEqual(score_for_line(line2, self.client, prefix=self.prefix), 100.0/3)
        self.assertEqual(score_for_line(line3, self.client, prefix=self.prefix), 50.0/3)
       
    def test_get_key_and_completion(self):
        """
        Ensure that get_key_and_completion finds the expected keys and completions based
        on key_length and completion_length
        """
        line = ['i', 'ate', 'a', 'peach']

        key, completion = get_key_and_completion(line, 2, 1, self.prefix)
        self.assertEqual(key, 'test:i:ate')
        self.assertEqual(completion, 'a')

        key, completion = get_key_and_completion(line, 2, 2, self.prefix)
        self.assertEqual(key, 'test:i:ate')
        self.assertEqual(completion, 'a:peach')

        key, completion = get_key_and_completion(line, 3, 2, self.prefix)
        self.assertEqual(key, 'test:i:ate:a')
        self.assertEqual(completion, 'peach')

        key, completion = get_key_and_completion(line, 4, 1, self.prefix)
        self.assertEqual(key, 'test:i:ate:a:peach')
        self.assertEqual(completion, markov.STOP)


    def test_generate(self):
        """
        Test the generate function
        """
        self.test_add_line_to_index()
        generated = generate(self.client, prefix=self.prefix, max_words=3)
        assert len(generated) >= 2
        assert len(generated) <= 3
        generated = generate(self.client, seed=['ate','one'], prefix=self.prefix, max_words=3)
        assert generated[2] == 'peach'
        assert 'sandwich' not in generated

        #test that relevant terms will be chosen when the relevant_terms argument is passed in
        generated = generate(self.client, relevant_terms=["peach",], prefix=self.prefix)       
        assert 'peach' in generated
        generated = generate(self.client, relevant_terms=["sandwich",], prefix=self.prefix)
        assert 'sandwich' in generated

        #there are no pizza keys!
        generated = generate(self.client, relevant_terms=["pizza",], prefix=self.prefix)
        assert len(generated) == 0

    def test_get_relevant_key_and_seed(self):
        """
        Test that get_relevant_key_and_seed functions as expected
        """
        #we get a key with sandwich in it
        self.test_add_line_to_index()
        key, seed = get_relevant_key_and_seed(self.client, relevant_terms=["sandwich",], prefix=self.prefix)
        assert "sandwich" in seed

        #pizza is not in our data set, so we get nothing
        key, seed = get_relevant_key_and_seed(self.client, relevant_terms=["pizza",], prefix=self.prefix)
        assert seed == []
        assert key is None
    
    def test_get_random_key_and_seed(self):
        """
        Test that get_random_key_and_seed functions as expected
        """
        self.test_add_line_to_index()
        key, seed = get_random_key_and_seed(self.client, prefix=self.prefix)
        assert len(seed) == 2
        assert self.prefix not in seed
        assert self.prefix in key

    def test_get_completion(self):
        """
        Test the get_completion method
        """
        self.test_add_line_to_index()
        key, seed = get_random_key_and_seed(self.client, prefix=self.prefix)
        if STOP not in seed:
            assert get_completion(self.client, key) is not None
        else:
            assert get_completion(self.client, key) is None
        key = "test:i:ate"
        assert get_completion(self.client, key) in ["a", "one"]
        #ensure that exclude works as expected
        assert get_completion(self.client, key, exclude=["a",]) == "one"
        assert get_completion(self.client, key, exclude=["a","one"]) is None

        #ensure that relevant_terms works as well
        assert get_completion(self.client, key, relevant_terms=["one",]) == "one"
        
            
    def tearDown(self):
        """
        clean up our redis keys
        """
        keys = self.client.keys(self.prefix+"*")
        for key in keys:
            self.client.delete(key)
    

class TestMarkovClass(unittest.TestCase):
    """
    Test that the Markov wrapper class behaves as expected
    """
    def setUp(self):
        self.markov = Markov(prefix="testclass", db=11)

    def test_add_line_to_index(self):
        line =  ['i','ate','a','peach']
        line1 = ['i','ate','one','peach']
        line2 = ['i','ate','a', 'sandwich']

        self.markov.add_line_to_index(line)
        self.markov.add_line_to_index(line1)
        self.markov.add_line_to_index(line2)
        self.assertEqual(self.markov.client.zscore("testclass:i:ate", "a"), 2.0)
        self.assertEqual(self.markov.client.zscore("testclass:ate:a", "peach"), 1.0)
                
    def test_score_for_line(self):
        self.test_add_line_to_index()
        line = ['i','ate','a','peach']
        self.assertEqual(self.markov.score_for_line(line), 100)
       
        
    def test_generate(self):
        self.test_add_line_to_index()
        generated = self.markov.generate(max_words=3)
        assert len(generated) >= 2
        assert len(generated) <= 3
        generated = self.markov.generate(seed=['ate','one'], max_words=3)
        assert 'peach' in generated 
        assert 'sandwich' not in generated

    def test_flush(self):
        m1 = Markov(prefix="one", db=5)
        m2 = Markov(prefix="two", db=5)

        line =  ['i','ate','a','peach']
        line1 = ['i','ate','one','peach']
        line2 = ['i','ate','a', 'sandwich']

        m1.add_line_to_index(line)
        m1.add_line_to_index(line1)
        m1.add_line_to_index(line2)

        important_line =  ['we', 'all', 'have', 'phones']

        m2.add_line_to_index(important_line)

        r = redis.Redis(db=5)
        assert len(r.keys("one:*")) == 6
        assert len(r.keys("two:*")) == 3

        m1.flush(prefix="one")

        assert len(r.keys("one:*")) == 0
        assert len(r.keys("two:*")) == 3

        m2.flush(prefix="two")

        assert len(r.keys("one:*")) == 0
        assert len(r.keys("two:*")) == 0        
        
    def tearDown(self):
        """
        clean up our redis keys
        """
        keys = self.markov.client.keys(self.markov.prefix+"*")
        for key in keys:
            self.markov.client.delete(key)
