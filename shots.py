"""
"""

from __future__ import division

import itertools
import math
import os
import sys
from collections import defaultdict, namedtuple
import simplejson as json
from operator import itemgetter

from ipdb import set_trace

# TODO
Datum = namedtuple('Datum', (
    'username',

    # bool: did they hit it?
    'success'))

def clear():
    os.system('clear')

def user_to_cost_str(data):
    s = []
    for user, cost in sorted(data.iteritems(), key=itemgetter(1), reverse=True):
        s.append('[%.2f] %s' % (cost, user))
    return '\n'.join(s)


# Don't really need all this...
def factorial(n):
    if n <= 2:
        return 1
    return n * factorial(n - 1)

def choose(n, k):
    return factorial(n) / (factorial(k) * factorial(n - k))

def binomial_pmf(k, n, p):
    return choose(n, k) * p**k * (1 - p)**(n - k)

def binomial_cdf(k, n, p):
    return sum(binomial_pmf(i, n, p) for i in range(int(math.floor(k))))

def calculate_bank_proportion(
    bank,
    target_bank,
    probability,
    pot,
    cost,
    probability_of_success_threshold = 0.75):
    """Find the best proportion of the cost to be put in the bank.

    We can calculate the expected number of shots until someone hits the bell
    (using the probability) and then calculate a proportion of the cost of each
    of those shots that should be sent to the bank in order to get the bank to
    reach the target bank amount in time.
    # TODO: ^^'s wrong, rewrite it.


    TODO: probably a way to not just simulate this.
    """

    """Calculate the minimum number of trials for which the probability that
    the bell will be hit at least once is greater than or equal to the threshold.


    """

    # We want the number of shots before the probability of there being a hit is
    # greater than the threshold.
    num_shots = 1
    for num_trials in itertools.count(1): #TODO: func me
        # Find the probability that any of the shots from the first until the
        # `num_trials`th will be a success. If that probability is greater than
        # the threshold, break and take the previous number.
        # Note that upping this probability puts more money in the bank, so we
        # should pipe it through from a top-level config.

        # TODO: do 1 - probability of getting 0 hits
        prob_of_a_hit = 1 - binomial_pmf(0, num_trials, probability)
        if prob_of_a_hit > probability_of_success_threshold:
            break

        num_shots += 1

    # Ok, so `num_shots` is how many shots we think we will have to add
    # `target_bank - bank` to the bank. Let's iterate over possible proportions
    # (proportion of cost to be put in bank) and try to find the lowest one that
    # puts enough money in the bank.
    #
    # Note that I'm using a single proportion for all of the shots (e.g. 1% of
    # the cost of each shot goes to the bank, for each of the N shots). This is
    # just easy-- maybe there's a better approach.

    delta = 0.01
    bank_proportion = 0.0
    while bank_proportion <= 0.99:
        bank_proportion += delta

        expected_money_made =  \
            simulate(target_bank - bank, bank_proportion, probability, pot, num_shots)
        if expected_money_made >= target_bank:
            return bank_proportion

    # If we get out of the loop it means that even if we put a large proportion 
    # of cost of each shot into the bank we can't get enough. We can just return
    # the high proportion.
    return bank_proportion


# TODO: comment and all that
def simulate(money_needed, bank_proportion, probability, pot, num_shots):
    money_banked = 0
    for _ in range(num_shots):
        cost = probability * pot
        bank_fee = cost * bank_proportion

        money_banked += bank_fee
        pot += cost - bank_fee

    return money_banked
        
        
        


# TODO: rewrite the main loop to handle exits cleanly
# TODO: serialize everything so that we don't lose track of money
if __name__ == '__main__':
    # Bank is savings to be used in the next pot. The pot is what's to be won
    # when someone hits the bell.
    bank = 0
    pot = 10

    # This is what we aim for the next pot to began at right after someone wins.
    target_bank = 10

    # If the bank hasn't grown enough when someone hits the bell then we turn
    # to the government (currently dselassi and cpollock) to cover the
    # difference. TODO: make sure we're not doing something dumb here.
    bailout_funds = 10


    # Prior of 0.02, to be updated after each shot.
    hits = 2
    shots = 100


    # TODO: needs to be serialized. State should be rebuildable from data file.
    winnings = defaultdict(float)
    dues = defaultdict(float)
    bailout_used = 0


    while True:
        probability = hits / shots

        cost = probability * pot
        print 'Pay $%.2f for a chance to win $%.2f' % (cost, pot)
        username = raw_input('Who are you? ')

        hit_response = raw_input('Did you hit it (y/n/c)? ')
        if hit_response == 'c':
            print 'canceling'
            continue


        elif hit_response == 'debug':
            print '## Debug ##'
            print 'probability: %f (%d of %d)' % (probability, hits, shots)
            print 'pot:', pot
            print 'bank:', bank
            print 'bailout: used=%d, left=%d' % (bailout_used, bailout_funds)
            print

            print '# Winnings #'
            print user_to_cost_str(winnings)

            print
            print '# Dues #'
            print user_to_cost_str(dues)
            print
            continue

        elif hit_response not in ('y', 'n'):
            print 'Invalid. Try again'
            continue


        #
        # Time to get real. Got either a hit or a miss.
        #
        dues[username] += cost

        # We use the cost paid by the player for this shot to grow the pot, but
        # we also want to put some money in the bank so that after a player hits
        # the bell we can use money from the bank to replenish the pot. Without
        # this we would need to use outside money to begin the pot.

        # So, how do we split the money between the two? If the bank grows too
        # slowly then we will occasionally begin new rounds with very small
        # pots, which could make the game uninteresting (Pay $0.0001 for a
        # a chance to win a few pennies!!!). If it grows too quickly then the
        # pot won't grow very quickly. Also, if the bank grows faster than we
        # anticipate then the current pot will remain small and the next one
        # will be too big.

        # One option here is to just manually set the proportion. E.g.:
        #   proportion_for_bank = 0.1

        # But instead we're doing something a bit more complicated. We figure out
        # how many shots we'll likely see before a winner, then we find a bank
        # proportion that will have us hit the desired bank in those shots.
        proportion_for_bank = calculate_bank_proportion(bank, target_bank, probability, pot, cost)
        bank += proportion_for_bank * cost
        pot += (1 - proportion_for_bank) * cost



        if hit_response == 'y':
            hits += 1
            shots += 1

            winnings[username] += pot

            # There's not enough in the bank. Time for a government bailout!
            if bank < target_bank:
                difference = target_bank - bank

                # If we don't have enough to do a bailout, use the lesser of the
                # remaining bailout funds and a single dollar. This single dollar
                # is tracked so that the government pays up later.
                if difference > bailout_funds:
                    difference = max(bailout_funds, 1)

                bailout_funds -= difference
                bailout_used += difference
                bank += difference


            # If we have more in the bank than needed, only use what's needed.
            pot = min(target_bank, bank)
            bank = bank - pot

            print '## Winnings ##'
            print user_to_cost_str(winnings)
            print


        elif hit_response == 'n':
            shots += 1

        else:
            assert False


        print '## Dues ##'
        print user_to_cost_str(dues)



        print
        print
        print
