"""
Tests for the markov package
"""
import redis
import unittest
import markov
from markov import Markov, add_line_to_index, make_key, max_for_key, min_for_key,\
     score_for_completion, score_for_line, get_key_and_completion

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
        self.markov = Markov(prefix="testclass",db=11)

    def test_add_line_to_index(self):
        line = ['i','ate','a','peach']
        line1 = ['i','ate','one','peach']
        line2 = ['i','ate','a', 'sandwich']

        self.markov.add_line_to_index(line)
        self.assertEqual(self.markov.client.zscore("testclass:i:ate", "a"), 1.0)
        self.assertEqual(self.markov.client.zscore("testclass:ate:a", "peach"), 1.0)

    def test_score_for_line(self):
        self.test_add_line_to_index()
        line = ['i','ate','a','peach']
        self.assertEqual(self.markov.score_for_line(line), 100)
        
    def tearDown(self):
        """
        clean up our redis keys
        """
        keys = self.markov.client.keys(self.markov.prefix+"*")
        for key in keys:
            self.markov.client.delete(key)
