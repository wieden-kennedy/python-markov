# Python-Markov

Python-Markov is a library for storing markov chains in a Redis database.  
You can use it to score lines for "good fit" or generate random texts based on your data.
This library is optimized for storing and scoring short pieces of text (sentences, tweets etc...).
Most of the functions are recursive, so don't go passing in a text of 1000+ words!

## Usage
Markov functions expects lists of tokens, you can add a line to your index like so.
    client = redis.Redis()
    line = ['some', 'words', 'that', 'you', 'would', 'like', 'to', 'add']	
    add_line_to_index(line, client, prefix="your_prefix")

you can score a line like so:
    line = ['another', 'list', 'of', 'words']
    score = score_for_line(line, client, prefix="your_prefix")
    #score will be something between 0 and 100

and you can generates line with or without a seed like so:
    # a purely random list based on your data
    list_of_words = generate(client, prefix="your_prefix")

    # a list starting with ['some', 'words'] no more that 3 words long
    list_of_words = generate(client, prefix="your_prefix", seed=['some', 'words'], max_words=3)