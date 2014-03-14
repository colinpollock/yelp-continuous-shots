"""
"""

from __future__ import division

import itertools
import simplejson as json
import math
import os
import sys
import time
from copy import copy
from collections import defaultdict, namedtuple
from operator import itemgetter
from sys import stderr

from ipdb import set_trace

datum_fields = (
    # Timestamp for when user hit y/n
    'time',

    'username',

    # Did they hit it? (bool)
    'success',

    # How much they paid to shoot.
    'cost',

    # What the pot is after the shot.
    'pot',

    # What the bank is after the shot.
    'bank',

    # What we want the bank to start at each round.
    'target_bank', 

    # Bailout funds available after the shot.
    'bailout_funds',
    
    # Bailout funds used after the shot.
    'bailout_funds_used',
    
    # dict from username to money won.
    'winnings',

    # dict from username to money owed.
    'dues',

    # How many shots have been taken overall.
    'shots',
    
    # How many of those shots were hits.
    'hits')


class Datum(namedtuple('Datum', datum_fields)):
    @staticmethod
    def from_dict(d):
        return Datum(**d)

    @property
    def to_dict(self):
        return dict((field, getattr(self, field)) for field in self._fields)

    def copy(self):
        return Datum.from_dict(self.to_dict)


def clear():
    os.system('clear')

def user_to_cost_str(data):
    s = []
    for user, cost in sorted(data.iteritems(), key=itemgetter(1), reverse=True):
        s.append('[%.2f] %s' % (cost, user))
    return '\n'.join(s)


# Don't really need all this... Just 1-P(zero hits)
def factorial(n):
    if n <= 2:
        return 1
    return n * factorial(n - 1)

def choose(n, k):
    return factorial(n) / (factorial(k) * factorial(n - k))

def binomial_pmf(k, n, p):
    return choose(n, k) * p**k * (1 - p)**(n - k)

def probability_of_no_hits(num_shots, probability):
    return 1 - binomial_pmf(0, num_shots, probability)


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
    for num_shots in itertools.count(2): #TODO: func me
        if probability_of_no_hits(num_shots, probability) > probability_of_success_threshold:
            break

    num_shots -= 1

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


        money_needed = target_bank - bank

        expected_money_made =  \
            simulate(money_needed, bank_proportion, probability, pot, num_shots)
        if expected_money_made >= money_needed:
            return bank_proportion

    # If we get out of the loop it means that even if we put a large proportion 
    # of cost of each shot into the bank we can't get enough. We can just return
    # the high proportion.
    return bank_proportion


def calc_cost(hits, shots, pot):
    probability = hits / shots
    cost = probability * pot

    # Round the cost to cents. Take the max of that and one cent.
    return max(0.01, round(cost, 2))

# TODO: comment and all that
# TODO: does this make sense?
def simulate(money_needed, bank_proportion, probability, pot, num_shots):
    money_banked = 0
    for _ in range(num_shots):


        bank_fee = cost * bank_proportion

        money_banked += bank_fee
        pot += cost - bank_fee

    return money_banked



def read_data(filepath):
    with open(filepath, 'r') as fh:
        return json.load(fh)


def show_debug(state):
    probability = state.hits / state.shots
    print '## Debug ##'
    print 'probability: %f (%d of %d)' % (probability, state.hits, state.shots)
    print 'pot:', state.pot
    print 'bank:', state.bank
    print 'bailout: used=%f, left=%f' % (state.bailout_funds_used, state.bailout_funds)
    print

    print '# Winnings #'
    print user_to_cost_str(state.winnings)

    print
    print '# Dues #'
    print user_to_cost_str(state.dues)
    print
    

if __name__ == '__main__':
    input_data_filepath = sys.argv[1]
    output_data_filepath = sys.argv[2]
    data = read_data(input_data_filepath)

    state = Datum.from_dict(data[-1])

    try:
        while True:
            probability = state.hits / state.shots
            pot = state.pot
            bank = state.bank

            winnings = dict(state.winnings)
            dues = dict(state.dues)
            shots = state.shots

            bailout_funds = state.bailout_funds
            bailout_funds_used = state.bailout_funds_used

            hits = state.hits

            cost = calc_cost(hits, shots, pot)

            print 'Pay $%.2f for a chance to win $%.2f' % (cost, pot)
            username = raw_input('Who are you (C to cancel)? ').strip()
            if username.lower() == 'c':
                continue

            elif username.lower() == 'debug':
                print
                show_debug(state)
                continue


            hit_response = raw_input('Did you hit it (y/n/cancel)? ')
            if hit_response not in ('y', 'n'):
                print >> sys.stderr, 'y or n plz'
                continue



            # Time to get real. Got either a hit or a miss. Time to track new state
            # for this shooter.

            # Debit the user.
            dues[username] = dues.get(username, 0) + cost

            shots += 1
            if hit_response == 'y':
                success = True
                hits += 1

                # Move the money from the pot to the user's credit.
                winnings[username] = winnings.get(username, 0) + pot
                pot = 0

            elif hit_response == 'n':
                success = False

            else:
                assert False



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

            # We figure out how many shots we'll likely see before a winner, then we
            # find a bank proportion that will have us hit the desired bank in those
            # shots.
            proportion_for_bank =  \
                calculate_bank_proportion(bank, state.target_bank, probability, pot, cost)

            bank += proportion_for_bank * cost
            pot += (1 - proportion_for_bank) * cost


            # Now we've paid the user. If the user won, we need to replenish the pot.
            if success:
                needed = state.target_bank - pot

                # There's not enough in the bank to reset the pot to our target.
                # Time for a government bailout!
                if bank < needed:
                    difference = needed - bank
                    # If we don't have enough bailout funds use the max of one
                    # dollar and half of the remaining bailout funds. This means
                    # it's possible for us to use a dollar that we don't have,
                    # which means the game runners have to put up additional
                    # dollars.
                    if difference > bailout_funds:
                        difference = max(1 / 2 * bailout_funds, 1)

                    # Subtract from bailout funds, not letting it go beneath 0.
                    bailout_funds = max(0, bailout_funds - difference)
                    bailout_funds_used = bailout_funds_used + difference
                    pot = bank + difference

                # There is enough money in the bank.
                else:
                    pot += needed
                    bank -= needed

                    # No bailouts, but have to hackily pass these around.
                    bailout_funds = bailout_funds
                    bailout_funds_used = bailout_funds_used



            print '## Winnings ##'
            print user_to_cost_str(winnings)
            print
            print

            print '## Dues ##'
            print user_to_cost_str(dues)
            print
            print



            new_state = Datum(
                time=time.time(),
                username=username,
                success=success,

                cost=cost,
                pot=pot,
                bank=bank,
                bailout_funds=bailout_funds,
                bailout_funds_used=bailout_funds_used,
                winnings=winnings,
                dues=dues,
                shots=shots,
                hits=hits,

                # Constant
                target_bank=state.target_bank,
            )

            data.append(new_state.to_dict)
            state = new_state

            init_pot = 5
            money_won = sum(state.winnings.values())
            money_spent = sum(state.dues.values())

            first = money_spent + init_pot + state.bailout_funds_used
            second = money_won + bank + pot
#            set_trace()
#            assert abs(first - second) < .01

            
    except EOFError:
        print >> stderr, 'Exiting'
        with open(output_data_filepath, 'w') as fh:
            json.dump(data, fh, indent=2)
        

# TODO: rewrite the main loop to handle exits cleanly
# TODO: serialize everything so that we don't lose track of money
