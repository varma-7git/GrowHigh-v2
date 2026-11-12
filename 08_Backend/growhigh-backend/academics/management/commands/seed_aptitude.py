"""Adds the Aptitude and Reasoning topics, each with notes, a solved example, practice questions and a topic task.

    py manage.py seed_aptitude

Safe to run again: lessons and questions that already exist are left alone.
"""
from django.core.management.base import BaseCommand

from academics.models import Guide
from academics import tracking
from academics.tracking import GuideQuestion, GuideTaskSetting
from accounts.models import User
from common.constants import Role


def M(text, opts, i, why):
    return ("MCQ", text, opts, i, why)


def N(text, answer, why):
    return ("NUMERIC", text, answer, why)


# (area, section, title, notes, task prompt, [questions])
LESSONS = [
    ("JOB_PREP", "aptitude", "Number System",
     "Types: natural (1, 2, 3...), whole (0, 1, 2...), integers, primes (only two factors: 1 and itself), composites.\nDivisibility: by 2 if the last digit is even; by 3 if the digit sum is divisible by 3; by 5 if it ends in 0 or 5; by 9 if the digit sum is divisible by 9.\nHCF = largest number dividing both; LCM = smallest number both divide. HCF x LCM = product of the two numbers.\nSolved example: HCF and LCM of 12 and 18. 12 = 2x2x3 and 18 = 2x3x3, so HCF = 2x3 = 6 and LCM = 2x2x3x3 = 36.",
     "Find the HCF and LCM of 36 and 48 using prime factors, and the sum of the first 20 natural numbers. Show every step.",
     [M("Which of these is a prime number?", ["21", "29", "39", "51"], 1, "29 has only 1 and 29 as factors. 21 = 3x7, 39 = 3x13, 51 = 3x17."),
      M("What is the HCF of 12 and 18?", ["3", "6", "9", "12"], 1, "Common prime factors are 2 and 3, so HCF = 6."),
      M("What is the LCM of 4 and 6?", ["10", "12", "18", "24"], 1, "Multiples of 4: 4, 8, 12. Multiples of 6: 6, 12. The first common one is 12."),
      M("A number is divisible by 3 when:", ["its last digit is 3", "the sum of its digits is divisible by 3", "it is even", "it ends in 0 or 5"], 1, "This is the divisibility rule for 3."),
      N("What is the LCM of 12 and 15?", "60", "12 = 2x2x3, 15 = 3x5, LCM = 2x2x3x5 = 60."),
      N("What is the sum of the first 10 natural numbers?", "55", "n(n+1)/2 = 10x11/2 = 55.")]),
    ("JOB_PREP", "aptitude", "Percentages", "", "",
     [N("What is 12% of 250?", "30", "250 x 12 / 100 = 30."),
      N("A number increased by 20% becomes 150. What was the number?", "125", "Original x 1.2 = 150, so original = 150 / 1.2 = 125.")]),
    ("JOB_PREP", "aptitude", "Profit and loss", "", "",
     [N("CP is Rs 400 and SP is Rs 500. What is the profit percentage?", "25", "Profit 100 / CP 400 x 100 = 25%."),
      N("An article bought for Rs 250 is sold at a 20% profit. What is the selling price in rupees?", "300", "250 x 120 / 100 = 300.")]),
    ("JOB_PREP", "aptitude", "Simple Interest",
     "Simple interest SI = P x R x T / 100, where P is the principal, R the yearly rate in % and T the time in years.\nAmount = P + SI.\nSolved example: SI on Rs 2,000 at 5% for 3 years = 2000 x 5 x 3 / 100 = Rs 300. Amount = Rs 2,300.",
     "Make up a loan or savings problem (principal, rate, time). Solve for the interest and the total amount, then change the time and show how the interest changes.",
     [M("What is the simple interest on Rs 1,000 at 5% per year for 2 years?", ["Rs 50", "Rs 100", "Rs 150", "Rs 200"], 1, "1000 x 5 x 2 / 100 = 100."),
      M("What principal earns Rs 150 simple interest at 5% in 3 years?", ["Rs 500", "Rs 1,000", "Rs 1,500", "Rs 2,000"], 1, "P = 150 x 100 / (5 x 3) = 1000."),
      M("At what rate does Rs 1,000 earn Rs 120 simple interest in 2 years?", ["5%", "6%", "8%", "12%"], 1, "R = 120 x 100 / (1000 x 2) = 6."),
      M("The amount after simple interest is:", ["P - SI", "P + SI", "P x SI", "SI / P"], 1, "Amount = principal + interest."),
      N("What is the simple interest in rupees on Rs 2,500 at 8% per year for 3 years?", "600", "2500 x 8 x 3 / 100 = 600."),
      N("What is the total amount in rupees on Rs 1,000 at 10% simple interest for 2 years?", "1200", "SI = 1000 x 10 x 2 / 100 = 200, so amount = 1200.")]),
    ("JOB_PREP", "aptitude", "Compound Interest",
     "In compound interest, interest is added to the principal each period.\nAmount A = P x (1 + R/100)^n (interest added yearly). CI = A - P.\nFor 2 years the difference CI - SI = P x (R/100)^2.\nSolved example: Rs 1,000 at 10% for 2 years. A = 1000 x 1.1 x 1.1 = 1210, so CI = 210 (SI would be 200).",
     "Compare Rs 10,000 invested for 3 years at 8% simple interest and at 8% compound interest (yearly). Show both amounts and the difference.",
     [M("What is the compound interest on Rs 1,000 at 10% for 2 years (yearly compounding)?", ["Rs 200", "Rs 210", "Rs 220", "Rs 121"], 1, "A = 1000 x 1.1^2 = 1210, CI = 210."),
      M("What is the CI minus SI on Rs 1,000 at 10% for 2 years?", ["Rs 0", "Rs 10", "Rs 20", "Rs 100"], 1, "P x (R/100)^2 = 1000 x 0.01 = 10."),
      M("What is the compound interest on Rs 2,000 at 5% for 1 year?", ["Rs 50", "Rs 100", "Rs 150", "Rs 200"], 1, "For one year CI equals SI: 2000 x 5 / 100 = 100."),
      M("Compound interest is greater than simple interest when the time is:", ["1 year", "more than 1 year", "less than 1 year", "never"], 1, "After the first period, interest earns interest."),
      N("What is the amount in rupees on Rs 5,000 at 10% compound interest for 2 years?", "6050", "5000 x 1.1 x 1.1 = 6050."),
      N("What is the compound interest in rupees on Rs 4,000 at 5% for 2 years?", "410", "4000 x 1.05 x 1.05 = 4410, so CI = 410.")]),
    ("JOB_PREP", "aptitude", "Ratio and Proportion",
     "A ratio a:b compares two quantities; simplify it by dividing both by their HCF.\nProportion: a:b = c:d means a x d = b x c.\nTo divide an amount N in the ratio a:b, the parts are N x a/(a+b) and N x b/(a+b).\nSolved example: divide Rs 100 in the ratio 2:3. Total parts 5, so the parts are 40 and 60.",
     "Share Rs 5,000 among three friends in the ratio 2:3:5 and show each share. Then make up one proportion problem about the speed of a bus and solve it.",
     [M("Simplify the ratio 24:36.", ["1:2", "2:3", "3:4", "4:5"], 1, "Divide both by 12."),
      M("If 4 : x = 12 : 15, what is x?", ["3", "5", "6", "10"], 1, "x = 4 x 15 / 12 = 5."),
      M("If a:b = 2:3 and b:c = 4:5, what is a:b:c?", ["2:3:5", "8:12:15", "4:6:5", "2:4:5"], 1, "Make b equal: a:b = 8:12 and b:c = 12:15."),
      M("Rs 100 is divided in the ratio 2:3. What is the larger part?", ["Rs 40", "Rs 50", "Rs 60", "Rs 70"], 2, "3/5 of 100 = 60."),
      N("Rs 270 is divided in the ratio 4:5. What is the smaller part in rupees?", "120", "270 x 4 / 9 = 120."),
      N("3 : 9 = 5 : ? Find the missing number.", "15", "? = 9 x 5 / 3 = 15.")]),
    ("JOB_PREP", "aptitude", "Averages",
     "Average = Sum of values / Number of values. So Sum = Average x Number.\nIf a new value is added, new average = (old sum + new value) / (old count + 1).\nSolved example: the average of 10, 20 and 30 is 60 / 3 = 20.",
     "Write down your marks in five subjects (real or imagined). Find the average, then find the mark you need in a sixth subject to raise the average by 2.",
     [M("What is the average of 10, 20 and 30?", ["15", "20", "25", "30"], 1, "60 / 3 = 20."),
      M("The average of 5 numbers is 12. What is their sum?", ["17", "48", "60", "72"], 2, "12 x 5 = 60."),
      M("What is the average of the first 5 natural numbers?", ["2", "3", "4", "5"], 1, "(1+2+3+4+5) / 5 = 3."),
      M("The average of 4 numbers is 15. A fifth number, 25, is added. What is the new average?", ["16", "17", "18", "20"], 1, "(60 + 25) / 5 = 17."),
      N("What is the average of 20, 30, 40, 50 and 60?", "40", "200 / 5 = 40."),
      N("A student's average over 6 subjects is 70. What is the total of the marks?", "420", "70 x 6 = 420.")]),
    ("JOB_PREP", "aptitude", "Time and Work",
     "If a person finishes a job in n days, one day's work is 1/n.\nWorking together, add the daily rates: A and B together do (1/a + 1/b) per day, so they need 1 / (1/a + 1/b) = ab / (a+b) days.\nMen x days = constant work (more men, fewer days).\nSolved example: A takes 10 days, B takes 15 days. Together: 1/10 + 1/15 = 5/30 = 1/6 per day, so 6 days.",
     "A has a pipe that fills a tank in 12 hours and another that fills it in 6 hours. Find the time to fill the tank with both open, and show each step.",
     [M("A takes 10 days and B takes 15 days for a job. How many days will they take together?", ["5", "6", "8", "12"], 1, "1/10 + 1/15 = 1/6 per day."),
      M("A does a job in 12 days. What fraction does A finish in 4 days?", ["1/4", "1/3", "1/2", "2/3"], 1, "4/12 = 1/3."),
      M("If 6 men finish a job in 10 days, how many days will 12 men need?", ["3", "5", "10", "20"], 1, "6 x 10 = 12 x d, so d = 5."),
      M("A person who does 1/8 of a job per day finishes it in:", ["4 days", "8 days", "16 days", "1/8 days"], 1, "Time is the reciprocal of the daily rate."),
      N("A takes 20 days and B takes 30 days. How many days do they take together?", "12", "1/20 + 1/30 = 5/60 = 1/12."),
      N("8 workers build a wall in 15 days. How many days will 10 workers need?", "12", "8 x 15 = 10 x d, so d = 12.")]),
    ("JOB_PREP", "aptitude", "Time, speed and distance", "", "",
     [N("How many hours does a 150 km journey take at 50 km/h?", "3", "Time = 150 / 50 = 3."),
      N("Convert 54 km/h to m/s.", "15", "54 x 5 / 18 = 15.")]),
    ("JOB_PREP", "aptitude", "Problems on Ages",
     "Define the unknown age as x, write the other ages in terms of x, then form an equation.\nRemember: after n years add n to every age; n years ago subtract n.\nThe difference between two people's ages never changes.\nSolved example: a father is 3 times as old as his son and their ages add up to 48. Son = x, father = 3x, so 4x = 48 and the son is 12.",
     "Make up an age problem about two members of your family using an equation. Solve it, then check your answer by substituting it back.",
     [M("A father is 3 times as old as his son. Their ages add up to 48. How old is the son?", ["10", "12", "14", "16"], 1, "x + 3x = 48, x = 12."),
      M("Ravi is 10 years older than Sita. In 5 years the sum of their ages will be 40. How old is Sita now?", ["10", "12", "15", "20"], 0, "Sita s, Ravi s+10. (s+5)+(s+15) = 40, so s = 10."),
      M("Five years ago a person was 20. How old is the person now?", ["15", "20", "25", "30"], 2, "20 + 5 = 25."),
      M("The age difference between two people:", ["grows every year", "shrinks every year", "never changes", "doubles every 10 years"], 2, "Both grow by the same number of years."),
      N("Two ages are in the ratio 3:5 and add up to 40. What is the larger age?", "25", "8 parts = 40, one part = 5, larger = 25."),
      N("A mother is 28 years older than her son. In 4 years she will be 3 times as old as him. How old is the son now?", "10", "s + 28 + 4 = 3(s + 4) gives s + 32 = 3s + 12, so s = 10. Check: she is 38 and he is 10; in 4 years she is 42 and he is 14, and 42 = 3 x 14.")]),
    ("JOB_PREP", "aptitude", "Probability",
     "Probability = Favourable outcomes / Total outcomes. It always lies between 0 (impossible) and 1 (certain).\nP(event) + P(not event) = 1.\nCoin: 2 outcomes. Die: 6 outcomes. Deck: 52 cards with 4 aces.\nSolved example: a bag has 3 red and 2 blue balls. P(red) = 3/5.",
     "A bag holds 5 red, 3 green and 2 blue balls. Write the probability of drawing each colour as a fraction and show they add up to 1.",
     [M("What is the probability of getting a head when a fair coin is tossed?", ["1/4", "1/3", "1/2", "1"], 2, "One favourable outcome out of two."),
      M("What is the probability of an even number when a die is rolled?", ["1/6", "1/3", "1/2", "2/3"], 2, "Even numbers 2, 4, 6 out of 6."),
      M("A bag has 3 red and 2 blue balls. What is the probability of drawing a red ball?", ["2/5", "3/5", "1/2", "3/2"], 1, "3 favourable out of 5."),
      M("What is the probability of drawing an ace from a deck of 52 cards?", ["1/52", "1/26", "1/13", "1/4"], 2, "4/52 = 1/13."),
      N("A box has 6 red and 4 blue pens. What is the probability, in percent, of picking a blue pen?", "40", "4/10 = 40%."),
      N("Two fair coins are tossed. What is the probability, in percent, of getting two heads?", "25", "1 of 4 equally likely outcomes.")]),
    ("JOB_PREP", "aptitude", "Permutations and Combinations",
     "Factorial: n! = n x (n-1) x ... x 1, so 5! = 120.\nPermutation (order matters): P(n, r) = n! / (n-r)!.\nCombination (order does not matter): C(n, r) = n! / (r! (n-r)!).\nSolved example: choosing 2 students from 5 for a team is C(5, 2) = 10. Choosing a captain and a vice-captain from 5 is P(5, 2) = 20.",
     "In your class group, pick a committee of 3 from 6 people. Calculate how many committees are possible and how many ways to choose a president, secretary and treasurer instead. Explain why the answers differ.",
     [M("What is 5! (5 factorial)?", ["25", "60", "120", "720"], 2, "5 x 4 x 3 x 2 x 1 = 120."),
      M("In how many ways can the letters of the word CAT be arranged?", ["3", "6", "9", "12"], 1, "3! = 6."),
      M("What is C(5, 2)?", ["5", "10", "20", "25"], 1, "5! / (2! x 3!) = 10."),
      M("What is P(5, 2)?", ["10", "20", "25", "60"], 1, "5 x 4 = 20."),
      N("In how many ways can 3 people be chosen from 6? (C(6, 3))", "20", "6! / (3! x 3!) = 20."),
      N("In how many ways can 4 different books be arranged in a row?", "24", "4! = 24.")]),
    ("JOB_PREP", "aptitude", "Data Interpretation",
     "Read the table or chart carefully: note the title, units and labels before calculating.\nUseful formulas: percentage change = (new - old) / old x 100; average = total / count; share = part / total x 100.\nSolved example: sales were 120, 150 and 180 in January, February and March. January to February rose by 30, which is 30/120 = 25%.",
     "Collect your own data, for example the number of study hours per day for a week. Write the numbers, calculate the total, the average and the day with the largest percentage change from the day before.",
     [M("Sales (units): Jan 120, Feb 150, Mar 180. What is the percentage increase from Jan to Feb?", ["20%", "25%", "30%", "50%"], 1, "30 / 120 x 100 = 25%."),
      M("Sales (units): Jan 120, Feb 150, Mar 180. What are the total sales over the three months?", ["400", "430", "450", "480"], 2, "120 + 150 + 180 = 450."),
      M("Marks: Maths 80, Physics 60, Chemistry 70. What percentage of the total marks (210) is Maths?", ["30%", "33.3%", "38.1%", "40%"], 2, "80 / 210 x 100 = 38.1%."),
      M("Expenses: Rent 5,000, Food 3,000, Travel 2,000. What fraction of the total is spent on food?", ["1/5", "3/10", "1/3", "2/5"], 1, "3000 / 10000 = 3/10."),
      N("Sales (units): Jan 120, Feb 150, Mar 180. What is the average monthly sales?", "150", "450 / 3 = 150."),
      N("Sales (units): Feb 150 and Mar 180. What is the percentage increase from Feb to Mar?", "20", "30 / 150 x 100 = 20%.")]),

    # ---------------- Reasoning
    ("JOB_PREP", "reasoning", "Number series", "", "",
     [M("What comes next? 2, 6, 12, 20, ?", ["28", "30", "32", "36"], 1, "Differences are 4, 6, 8, so the next difference is 10 and the next number is 30."),
      M("What comes next? 1, 1, 2, 3, 5, ?", ["6", "7", "8", "9"], 2, "Each term is the sum of the previous two (Fibonacci)."),
      M("What comes next? 100, 90, 80, 70, ?", ["50", "60", "65", "75"], 1, "Subtract 10 each time.")]),
    ("JOB_PREP", "reasoning", "Alphabet Series",
     "Write the position of each letter (A=1 ... Z=26) and look for a pattern in the positions.\nPositions: A1 B2 C3 D4 E5 F6 G7 H8 I9 J10 K11 L12 M13 N14 O15 P16 Q17 R18 S19 T20 U21 V22 W23 X24 Y25 Z26.\nSolved example: A, C, E, G, ? The positions go 1, 3, 5, 7 so the next is 9, which is I.",
     "Create three alphabet series of your own with different rules (for example +2, -3, increasing gaps). Give the next two letters and the rule for each.",
     [M("What comes next? A, C, E, G, ?", ["H", "I", "J", "K"], 1, "Positions rise by 2: 1, 3, 5, 7, 9 = I."),
      M("What comes next? Z, X, V, T, ?", ["S", "R", "Q", "P"], 1, "Positions fall by 2: 26, 24, 22, 20, 18 = R."),
      M("What comes next? B, D, G, K, ?", ["N", "O", "P", "Q"], 2, "Positions 2, 4, 7, 11 differ by 2, 3, 4, so the next difference is 5 and the position is 16 = P."),
      M("What comes next? AZ, BY, CX, ?", ["DW", "DV", "EW", "CW"], 0, "The first letter moves forward and the second moves back: D and W.")]),
    ("JOB_PREP", "reasoning", "Coding and Decoding",
     "A code replaces letters by other letters or numbers by a fixed rule. Find the rule from the example, then apply it.\nCommon rules: shift each letter by a fixed number, reverse the word, use alphabet positions.\nSolved example: if CAT is coded as DBU (each letter moves one forward), then DOG is EPH.",
     "Invent a letter-shift code of your own, write a short message in it (at least 5 words) and give the rule so a classmate can decode it.",
     [M("If CAT is coded as DBU, how is DOG coded?", ["EPH", "ENH", "CNF", "EOG"], 0, "Each letter moves one forward: D to E, O to P, G to H."),
      M("If A=1, B=2, C=3 and so on, what is the code for BAD?", ["214", "123", "412", "241"], 0, "B=2, A=1, D=4."),
      M("If CODE is written as DPEF, how is BOLD written?", ["CPME", "CPLE", "APKC", "CNME"], 0, "Each letter moves one forward: B to C, O to P, L to M, D to E."),
      M("If ROSE is coded as TQUG (each letter moves two forward), how is LOVE coded?", ["NQXG", "MPWF", "NPXG", "NQWG"], 0, "L to N, O to Q, V to X, E to G.")]),
    ("JOB_PREP", "reasoning", "Blood relations", "", "",
     [M("A is the brother of B. B is the mother of C. How is A related to C?", ["Father", "Maternal uncle", "Paternal uncle", "Grandfather"], 1, "A is the brother of C's mother."),
      M("Pointing to a man, a woman says: 'He is the son of my father's only son.' How is the man related to her?", ["Son", "Nephew", "Brother", "Cousin"], 1, "Her father's only son is her brother, so the man is her brother's son: her nephew.")]),
    ("JOB_PREP", "reasoning", "Direction Sense",
     "The four main directions are North, East, South, West, with North-East and the others between them.\nFacing North: right is East, left is West. Turning right rotates clockwise: N, E, S, W.\nFor a path with a right angle, the distance from the start is by Pythagoras: d = square root of (a^2 + b^2).\nSolved example: walk 3 km west then 4 km north. The distance from the start is 5 km.",
     "Draw a short walking route from your home to your college with at least three turns. Write the directions you walk, then work out in which direction and how far your college is from home in a straight line.",
     [M("A man faces east and turns left. Which direction does he face now?", ["North", "South", "West", "East"], 0, "Left of east is north."),
      M("A man faces north and turns right. Which direction does he face now?", ["East", "West", "South", "North"], 0, "Right of north is east."),
      M("A person walks 3 km west and then 4 km north. How far is the person from the start?", ["5 km", "6 km", "7 km", "1 km"], 0, "Square root of 3^2 + 4^2 = 5."),
      M("A man walks 5 km north then 5 km east. In which direction is he from the start?", ["North-East", "South-East", "North-West", "East"], 0, "He has moved both north and east."),
      N("A person walks 6 km north and then 8 km east. How many km is the person from the start?", "10", "Square root of 36 + 64 = 10.")]),
    ("JOB_PREP", "reasoning", "Seating Arrangements",
     "Draw a row or a circle and fill in the fixed facts first. Count positions from the left or from the right carefully.\nRow of n people: position from the right = n - (position from the left) + 1.\nSolved example: in a row of 7, Rahul is 3rd from the left. From the right he is 7 - 3 + 1 = 5th.",
     "Arrange five of your friends in a row using four clues you write yourself (for example 'A sits next to B'). Give the clues and the final order so that the answer is unique.",
     [M("In a row of 7, Rahul is 3rd from the left. What is his position from the right?", ["3rd", "4th", "5th", "6th"], 2, "7 - 3 + 1 = 5."),
      M("In a row of 20, X is 8th from the left. What is X's position from the right?", ["11th", "12th", "13th", "14th"], 2, "20 - 8 + 1 = 13."),
      M("Five friends sit in a row. A is at the left end and C is at the right end. B sits next to A and D sits next to C. Who sits in the middle?", ["B", "D", "E", "A"], 2, "The order is A, B, E, D, C so E is in the middle."),
      M("In a line, Mohan is 6th from the front and 10th from the back. How many students are in the line?", ["14", "15", "16", "17"], 1, "6 + 10 - 1 = 15.")]),
    ("JOB_PREP", "reasoning", "Puzzles",
     "Read every clue, list what you know, and eliminate options one at a time.\nTip: when comparing people, write them in order on a line (for example tallest to shortest).\nSolved example: A is taller than B, and B is taller than C. So A > B > C and C is the shortest.",
     "Write one logic puzzle with three people and three clues, give its solution, and explain how each clue narrows the answer.",
     [M("A is taller than B and B is taller than C. Who is the shortest?", ["A", "B", "C", "Cannot say"], 2, "A > B > C."),
      M("Two coins add up to 30 paise and one of them is not a 5 paise coin. Which coins are they?", ["25 paise and 5 paise", "20 paise and 10 paise", "15 paise and 15 paise", "Not possible"], 0, "One coin is not 5 paise, but the other one is: 25 + 5 = 30."),
      M("Tom is older than Dick. Dick is older than Harry. Which statement must be true?", ["Harry is older than Tom", "Tom is older than Harry", "Dick is the youngest", "Tom and Harry are the same age"], 1, "Tom > Dick > Harry."),
      M("If 5 machines make 5 items in 5 minutes, how many minutes do 100 machines need to make 100 items?", ["5", "20", "50", "100"], 0, "Each machine makes one item in 5 minutes, so 100 machines make 100 items in 5 minutes.")]),
    ("JOB_PREP", "reasoning", "Analogy",
     "Find the relationship between the first pair, then apply the same relationship to the second pair.\nCommon relationships: tool and action, place and worker, part and whole, animal and ability.\nSolved example: Pen : Write :: Knife : Cut. A pen is used to write; a knife is used to cut.",
     "Write four analogies of your own, each with a different relationship (for example tool and use, place and person). Name the relationship in each.",
     [M("Pen : Write :: Knife : ?", ["Cut", "Sharp", "Kitchen", "Steel"], 0, "A pen is used to write and a knife is used to cut."),
      M("Doctor : Hospital :: Teacher : ?", ["School", "Book", "Student", "Class"], 0, "A doctor works in a hospital and a teacher works in a school."),
      M("Bird : Fly :: Fish : ?", ["Water", "Swim", "Fins", "Scales"], 1, "A bird flies and a fish swims."),
      M("Finger : Hand :: Petal : ?", ["Flower", "Leaf", "Tree", "Root"], 0, "A finger is a part of a hand, and a petal is a part of a flower.")]),
    ("JOB_PREP", "reasoning", "Classification",
     "Find the item that does not belong with the others. Look for a shared property such as category, number type or shape.\nSolved example: Apple, Mango, Potato, Banana. Potato is a vegetable; the others are fruits.",
     "Make three odd-one-out questions of your own from your branch subjects, with four options each, and explain which one is different and why.",
     [M("Choose the odd one out.", ["Apple", "Mango", "Potato", "Banana"], 2, "Potato is a vegetable and the rest are fruits."),
      M("Choose the odd one out.", ["2", "3", "5", "9"], 3, "2, 3 and 5 are prime and 9 is not."),
      M("Choose the odd one out.", ["Python", "Java", "C++", "MySQL"], 3, "MySQL is a database; the rest are programming languages."),
      M("Choose the odd one out.", ["Square", "Triangle", "Circle", "Cube"], 3, "A cube is three-dimensional; the others are flat shapes.")]),
    ("JOB_PREP", "reasoning", "Syllogisms",
     "A syllogism gives two statements and asks which conclusion must follow. Use only the statements, never outside knowledge.\nAll A are B and All B are C means All A are C.\nAll A are B and No B is C means No A is C.\nSome A are B and All B are C means Some A are C.",
     "Write two syllogisms of your own: one with a valid conclusion and one where the conclusion does not follow. Explain with a diagram in words (circles inside circles).",
     [M("Statements: All cats are animals. All animals are living. Conclusion: All cats are living.", ["Follows", "Does not follow", "Cannot say", "Only some follow"], 0, "A is inside B and B is inside C, so A is inside C."),
      M("Statements: Some pens are books. All books are papers. Conclusion: Some pens are papers.", ["Follows", "Does not follow", "Cannot say", "No pen is paper"], 0, "The pens that are books are also papers."),
      M("Statements: All A are B. No B is C. Conclusion: No A is C.", ["Follows", "Does not follow", "Some A are C", "Cannot say"], 0, "A lies inside B, and B has no overlap with C."),
      M("Statements: All roses are flowers. Some flowers fade. Conclusion: Some roses fade.", ["Follows", "Does not follow", "All roses fade", "No rose fades"], 1, "The flowers that fade may not include any rose.")]),
    ("JOB_PREP", "reasoning", "Statement and Conclusion",
     "A conclusion follows only if it is certainly true given the statement. If it may or may not be true, it does not follow.\nWatch for words like 'all', 'only', 'always' in a conclusion: they make it very strong and it usually does not follow.\nSolved example: Statement: Some engineers are artists. Conclusion: All engineers are artists. This does not follow.",
     "Write three statements from your college life and, for each, one conclusion that follows and one that does not. Explain why.",
     [M("Statement: Some engineers are artists. Conclusion: All engineers are artists.", ["Follows", "Does not follow", "Definitely true", "Cannot say anything"], 1, "'Some' does not allow us to say 'all'."),
      M("Statement: All students who pass the exam receive a certificate. Ravi passed. Conclusion: Ravi receives a certificate.", ["Follows", "Does not follow", "Cannot say", "Ravi failed"], 0, "The rule applies to everyone who passes."),
      M("Statement: The library is open only on weekdays. Conclusion: The library is open on Sunday.", ["Follows", "Does not follow", "Cannot say", "Open on all days"], 1, "Sunday is not a weekday."),
      M("Statement: Rahul scored more than Mohan, and Mohan scored more than Ajay. Conclusion: Rahul scored more than Ajay.", ["Follows", "Does not follow", "Cannot say", "Ajay scored the highest"], 0, "Rahul > Mohan > Ajay.")]),
    ("JOB_PREP", "reasoning", "Non-Verbal Reasoning",
     "Non-verbal reasoning is about shapes, rotations, reflections and counting figures.\nRotation 90 degrees clockwise: top goes to right, right goes to bottom, bottom goes to left, left goes to top.\nA mirror image flips left and right (vertical mirror).\nSolved example: a triangle pointing up, rotated 180 degrees, points down.",
     "Describe in words a figure of your own (for example an arrow pointing up). Rotate it 90 degrees clockwise and then reflect it in a vertical mirror, and describe the figure after each step.",
     [M("A square is rotated 90 degrees clockwise. The side that was at the top is now on the:", ["Right", "Left", "Bottom", "Top"], 0, "Clockwise: top moves to right."),
      M("An arrow points up. After rotating 180 degrees it points:", ["Up", "Down", "Left", "Right"], 1, "A half turn reverses the direction."),
      M("How many sides does a hexagon have?", ["5", "6", "7", "8"], 1, "A hexagon has six sides."),
      M("The mirror image of the letter 'b' in a vertical mirror (left and right swapped) looks like:", ["d", "p", "q", "b"], 0, "Flipping left and right turns b into d.")]),
]


class Command(BaseCommand):
    help = "Add Aptitude and Reasoning topics with notes, practice questions (MCQ and numerical) and topic tasks."

    def handle(self, *args, **opts):
        tracking.SILENT = True  # loading lessons in bulk should not notify students
        try:
            self._run()
        finally:
            tracking.SILENT = False

    def _run(self):
        admin = User.objects.filter(role=Role.ADMIN, is_active=True).order_by("id").first()
        order0 = 100
        made = qn = 0
        for n, (area, section, title, notes, task, questions) in enumerate(LESSONS):
            g = Guide.objects.filter(area=area, section=section, title=title).first()
            if not g:
                g = Guide.objects.create(area=area, section=section, kind="NOTES", title=title, body=notes, order_no=order0 + n, uploaded_by=admin)
                GuideTaskSetting.objects.create(guide=g, task_type="WRITTEN", prompt=task)
                made += 1
            have = set(GuideQuestion.objects.filter(guide=g).values_list("text", flat=True))
            i = len(have)
            for q in questions:
                if q[1] in have:
                    continue
                if q[0] == "MCQ":
                    _, text, o, correct, why = q
                    GuideQuestion.objects.create(guide=g, qtype="MCQ", text=text, option_a=o[0], option_b=o[1], option_c=o[2], option_d=o[3], correct=correct, explanation=why, order_no=i)
                else:
                    _, text, ans, why = q
                    GuideQuestion.objects.create(guide=g, qtype="NUMERIC", text=text, answer=ans, explanation=why, order_no=i)
                i += 1
                qn += 1
        self.stdout.write(self.style.SUCCESS(f"Done. Added {made} lessons and {qn} practice questions."))
