# Python-Markov

Python-Markov is a python library for storing Markov chains in a Redis database.  
You can use it to score lines for "good fit" or generate random texts based on your collected data.
This library is optimized for storing and scoring short pieces of text (sentences, tweets etc...).

## Markov Chains
*Q: What is a Markov Chain and why would I use this library?*

A: In mathematical terms, a Markov Chain is a sequence of values where the next value depends only on the current value (and not past values).  It's 
basically a really simple state machine, where given the present state, the future state is conditionally independent of the past.

Markov chains have many real-world applications. For example, [Google's Page Rank](http://ilpubs.stanford.edu:8090/422/) algorithm is essentially a 
Markov chain over a graph of the web.  

One of the simplest and most well known applications of Markov Chains is generating "realistic" looking texts based on some set
of input texts.

In the case of text, a Markov Chain could be used to answer the question, "Given the present word (or set of words), which words might possibly follow?".
You could also use Markov Chains to answer the question, "Given the present word, how likely is it that this word I've chosen would be the next?".

The goal of Python-Markov is to store Markov chains that model your choice of text.  You can use the included methods to generate new pieces of
text that resemble your input values. You can also score a given piece of text for "good fit" with your data set.

When you add a piece of text to Python-Markov, it breaks it down in to keys and possible completions, with a frequency.
For example, let say you had two sentences:
```
"I ate a pizza."
and 
"I ate a sandwich."
```

If you use 2 word keys and 1 word competions, when you add these sentences to your model you'd end up with something like this:
```
key:"I ate" completions: [ (text: "a", frequency: 2) ]
key:"ate a" completions: [ (text: "pizza", frequency: 1), (text: "sandwich", frequency: 1)]
key:"a sandwich" completions: [(text: EOL, frequency: 1)]

and so on....
```
Even with the small set of data you can generate text. For each possible 2 word key, there's a maximum of two possible completions,  if you were to start a random walk across your
data with "I ate", it would always be followed by "a". The next key, "ate a", could be followed by "pizza" or "sandwich", and
the keys "a pizza" and "a sandwich" will always be followed by EOL (end of line). While you can generate with a small data set, you'll
need a lot of data to build longer, more interesting texts.

You could also use the data mode to ascertain that "I ate one hammer" doesn't fit the model well, and isn't a thing that anyone would say ever. 

You can read more about Markov Chains [here](http://en.wikipedia.org/wiki/Markov_chain) or [here](http://mathworld.wolfram.com/MarkovChain.html).

*Q: Can I store things that aren't text with Python-Markov?*

A: Yes, as long as it can be coerced to something Redis friendly.  You could theoretically put any sort of Python-thing into
python-markov, score sequences of those things for fit, and generate new sequences of things.

## Installation
Use pip!
``` pip install -e git+https://github.com/wieden-kennedy/python-markov#egg=markov ```

## Usage

The functions in python-markov expect lists of tokens.  For example, to add a single line of text to your Markov chain, you can
call add_line_to_index() like so.

```python   
import redis
from markov.markov import add_line_to_index

client = redis.Redis()
line = ['some', 'words', 'that', 'you', 'would', 'like', 'to', 'add']	
add_line_to_index(line, client, prefix="your_prefix")
```

Your Markov chain is namespaced by a prefix (so you can store different data sets in the same Redis database). Each of the functions
in the markov modules takes a prefix argument to determine which set of data to use.  To make things easier, there's a Markov
class that allows you to refer to a specific set of prefixed data.

```python
from markov import Markov

twitter_data = Markov(prefix="twitter")
twitter_data.add_line_to_index(["eating", "sushi", "with", "my", "cat"])
```

It's recommended that you use the Markov class to add texts to your model, score texts and generate new text.

For example, let's say you've collected a lot of Oprah transcripts and stored them in your model. Scoring a text
would look something like this:
```python
from markov import Markov

#oprah_data is a Markov model filled with Oprah quotes
oprah_data = Markov(prefix="oprah")

#sentence is our guess at something Oprah might say
sentence = ["you", "get", "a", "car"]

#let's ask oprah_data how we did
score = oprah_data.score_for_line(sentence)
# at this point, score is probably something like 100

other_sentence = ["you", "get", "rusty", "razor", "blades"]

score = oprah_data.score_for_line(other_sentence)
#since oprah probably never said this the score is probably much lower, like 30 or 50
```

You can also generate text from your Markov model. Let's say you put a bunch of tweets in your model and you wanted
to generate a representative sample:

```python
from markov import Markov

tweet_data = Markov(prefix="tweets")

new_tweet = tweet_data.generate(max_words=6)
#new_tweet will be something like ["omg", "i", "love", "snax"]
```

If you want your text to start with a certain key, you can seed it like so:

```python
new_tweet = tweet_data.generate(seed=['i','love'], max_words=6)
#new_tweet will be something like ['i', 'love', 'to', 'eat', 'snax']
```

you can use the max_words argument to determine the maximum number of tokens to include in the generated sequence
```python
new_tweet = tweet_data.generate(max_words=100)
#new tweet could be 2-100 words long
```

if not, Markov.generate() will continue to generate texts up to 1000 words long by default until it choses a STOP character
at which point it will stop.

```python
new_tweet = tweet_data.generate()
#new tweet could be really long, or not!
```

