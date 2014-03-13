Yelp Continuous Shots
=====================

This is similar to Friday Shots, but happens continuously rather than on Fridays.
Anyone can take a shot any time, and if they hit the bell they take the full pot
right away. The program displays two things:
1) How much it costs to take one shot.
2) How much the shooter will win if they hit the bell.


If necessary we can create a queue. 

Details
-------
We track how many shots have been taken and how many of those have been hits. We
use `hits / shots` as the probability of a hit. Note that this is overall, not
per player.

Each shot costs `probability_of_hit * pot`. Part of the cost of each shot is
added to pot. The rest of it is added to a "bank" that is used to replenish the
pot after someone wins. We try to put enough money into the bank so that by the
time someone wins a round there'll be $10 ready.



TODO
----
* Handle serialization
* Make it so that the program can quit at any time
* We say that the user will win $POT, but then give them $POT + $COST. We should
  pay out and then put the cost back into the pot and bank.
* Print out winners - dues for each user.
* Clean up the code.


Error Cases
-----------
* If someone hits the bell before the bank has grown then the government bailout
  is used. After the bailout money is used, all future bailings (initial pots)
  are just $1. Once we make it possible to kill and restart the program, we could
  just alter the bailout funds available field (and agree to donate the money).


