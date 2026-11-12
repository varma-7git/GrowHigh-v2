"""Adds lessons to Job preparation, Career growth and Communication. Each lesson has notes, practice questions
on its own topic, and a hands-on task about the same topic.

    py manage.py seed_lessons

Safe to run again: a lesson that already exists (same area, section and title) is left alone.
"""
from django.core.management.base import BaseCommand

from academics.models import Guide
from academics import tracking
from academics.tracking import GuideQuestion, GuideTaskSetting
from accounts.models import User
from common.constants import Role

W, U, R = "WRITTEN", "UPLOAD", "RECORDING"

# (area, section, title, notes, task type, task prompt, [(question, [4 options], correct index, explanation)])
LESSONS = [
    # ---------------- Job preparation: Aptitude
    ("JOB_PREP", "aptitude", "Percentages",
     "Percent means 'out of 100'.\n- x% of N = N x x / 100\n- Percentage change = (new - old) / old x 100\n- Successive changes multiply: a 10% rise then a 10% fall is 1.10 x 0.90 = 0.99 of the original.",
     W, "A shop gives 15% off a Rs 1,200 bag, then adds 5% tax on the discounted price. Show each step and the final price you pay.",
     [("What is 25% of 80?", ["15", "20", "25", "30"], 1, "80 x 25 / 100 = 20."),
      ("A price rises from Rs 200 to Rs 250. What is the percentage increase?", ["20%", "25%", "50%", "125%"], 1, "Change 50 / old 200 x 100 = 25%."),
      ("40% of a number is 60. What is the number?", ["24", "100", "150", "240"], 2, "60 x 100 / 40 = 150."),
      ("A student scores 45 out of 60. What is the percentage?", ["65%", "70%", "75%", "80%"], 2, "45 / 60 x 100 = 75%.")]),
    ("JOB_PREP", "aptitude", "Time, speed and distance",
     "Speed = Distance / Time.\n- To change km/h to m/s multiply by 5/18; m/s to km/h multiply by 18/5.\n- Two objects moving towards each other close the gap at the sum of their speeds.\n- A train crossing a pole travels its own length.",
     W, "Two stations are 180 km apart. A train leaves A at 8:00 am at 60 km/h. Another leaves B towards A at 9:00 am at 40 km/h. At what time do they meet? Show every step.",
     [("How long does 60 km take at 40 km/h?", ["1 hour", "1.5 hours", "2 hours", "2.5 hours"], 1, "Time = 60 / 40 = 1.5 hours."),
      ("Convert 72 km/h to m/s.", ["15 m/s", "18 m/s", "20 m/s", "25 m/s"], 2, "72 x 5/18 = 20."),
      ("A 100 m train crosses a pole in 10 seconds. What is its speed?", ["5 m/s", "10 m/s", "20 m/s", "100 m/s"], 1, "100 m / 10 s = 10 m/s."),
      ("How far is covered in 3 hours at 55 km/h?", ["155 km", "160 km", "165 km", "170 km"], 2, "55 x 3 = 165.")]),
    ("JOB_PREP", "aptitude", "Profit and loss",
     "Profit = Selling price (SP) - Cost price (CP). Loss = CP - SP.\n- Profit % = Profit / CP x 100\n- SP = CP x (100 + profit%) / 100\n- Percentages in profit and loss are always on the cost price unless the question says otherwise.",
     W, "Make up a small business problem (for example selling phone covers) with a cost price, a selling price and a discount. Solve it step by step and give the profit percentage.",
     [("CP is Rs 500 and SP is Rs 600. What is the profit percentage?", ["10%", "15%", "20%", "25%"], 2, "Profit 100 / 500 x 100 = 20%."),
      ("An item costs Rs 800 and is sold at a 25% loss. What is the SP?", ["Rs 550", "Rs 600", "Rs 650", "Rs 700"], 1, "800 x 75 / 100 = 600."),
      ("SP is Rs 450 with a 50% profit. What is the CP?", ["Rs 225", "Rs 300", "Rs 350", "Rs 400"], 1, "450 / 1.5 = 300."),
      ("A loss happens when:", ["SP is more than CP", "SP is equal to CP", "SP is less than CP", "CP is zero"], 2, "Loss means you sold for less than you paid.")]),
    # ---------------- Reasoning
    ("JOB_PREP", "reasoning", "Number series",
     "Look for the rule between neighbouring terms: add or subtract a fixed number, multiply by a fixed number, squares, cubes, or alternating rules.\nTip: write the differences between terms first. If the differences are not constant, check the ratios.",
     W, "Write three number series of your own: one with an add/subtract rule, one with a multiply rule and one with squares. Give the next two terms and the rule for each.",
     [("2, 4, 8, 16, ?", ["24", "30", "32", "36"], 2, "Each term doubles."),
      ("3, 6, 9, 12, ?", ["14", "15", "16", "18"], 1, "Add 3 each time."),
      ("1, 4, 9, 16, ?", ["20", "24", "25", "36"], 2, "These are squares: 1, 2, 3, 4, 5 squared."),
      ("5, 10, 20, 40, ?", ["60", "70", "80", "100"], 2, "Each term doubles.")]),
    ("JOB_PREP", "reasoning", "Blood relations",
     "Break a statement into small steps and draw a family tree.\n- Father's father or mother's father is a grandfather.\n- Father's or mother's brother is an uncle; father's or mother's sister is an aunt.\n- Uncle's or aunt's children are cousins.",
     W, "Describe your own family tree across three generations in text. Then write three blood-relation questions from it, with their answers.",
     [("A woman points to a man and says, 'He is the son of my mother's only brother.' How is he related to her?", ["Brother", "Uncle", "Cousin", "Nephew"], 2, "Her mother's brother is her uncle; his son is her cousin."),
      ("Your father's sister's husband is your:", ["Grandfather", "Uncle", "Brother", "Nephew"], 1, "Your father's sister is your aunt; her husband is your uncle."),
      ("A is B's brother and B is C's mother. How is A related to C?", ["Father", "Maternal uncle", "Cousin", "Grandfather"], 1, "A is the brother of C's mother, so C's maternal uncle."),
      ("Your mother's mother is your:", ["Aunt", "Maternal grandmother", "Sister", "Daughter"], 1, "The mother of your mother is your maternal grandmother.")]),
    # ---------------- Coding
    ("JOB_PREP", "coding", "Strings in Python: reverse and palindrome",
     "Strings are immutable: you create new strings, you never change one in place.\n- s[::-1] gives the reversed string.\n- len(s) gives the length; s.lower() makes lowercase; s.replace(' ', '') removes spaces.\n- A palindrome reads the same forwards and backwards.",
     W, "Write a Python function is_palindrome(s) that ignores case and spaces. Paste your code and show two inputs with the output you expect for each.",
     [("What does 'abc'[::-1] give?", ["abc", "cba", "bca", "An error"], 1, "The step -1 walks the string backwards."),
      ("Strings in Python are:", ["Mutable", "Immutable", "Lists", "Numbers"], 1, "You cannot change a string in place."),
      ("What does len('hello') return?", ["4", "5", "6", "Error"], 1, "There are 5 characters."),
      ("Which line loops over each character of s?", ["for ch in s:", "loop ch of s", "foreach s", "while s.each"], 0, "Python uses for ... in.")]),
    ("JOB_PREP", "coding", "Lists and loops: finding the largest number",
     "A list holds ordered items: nums = [3, 9, 2]. Indexing starts at 0.\n- for n in nums: visits each item.\n- Keep a variable 'largest' and update it when you see a bigger number.\n- Built-ins: max(nums), min(nums), sum(nums), len(nums).",
     W, "Write code that finds the second largest number in a list without sorting it. Paste the code and explain it in two lines.",
     [("What does max([3, 9, 2]) return?", ["3", "9", "2", "14"], 1, "9 is the largest."),
      ("What is the index of the first item in a list?", ["0", "1", "-1", "It depends"], 0, "Python counts from 0."),
      ("What does sum([1, 2, 3]) return?", ["5", "6", "7", "123"], 1, "1 + 2 + 3 = 6."),
      ("What does list(range(3)) give?", ["[1, 2, 3]", "[0, 1, 2]", "[0, 1, 2, 3]", "[3]"], 1, "range(3) starts at 0 and stops before 3.")]),
    # ---------------- Technical interview
    ("JOB_PREP", "technical", "SQL basics: SELECT, WHERE and GROUP BY",
     "SELECT chooses columns, FROM names the table, WHERE filters rows, GROUP BY groups rows, ORDER BY sorts (ascending by default).\n- COUNT(*) counts rows.\n- A primary key uniquely identifies each row.\nExample: SELECT branch, COUNT(*) FROM students GROUP BY branch;",
     W, "A table students(id, name, branch, marks) exists. Write SQL to (a) list the names of CSE students with marks above 60 and (b) count the students in each branch. Paste both queries.",
     [("Which clause filters rows?", ["ORDER BY", "WHERE", "GROUP BY", "LIMIT"], 1, "WHERE keeps only the rows that match."),
      ("Which function counts rows?", ["SUM", "COUNT(*)", "TOTAL", "ROWS"], 1, "COUNT(*) counts rows."),
      ("ORDER BY sorts in which order by default?", ["Descending", "Ascending", "Random", "It does not sort"], 1, "Ascending unless you write DESC."),
      ("A primary key:", ["Can repeat", "Uniquely identifies a row", "Is always text", "Is optional in every table"], 1, "It identifies each row and cannot repeat.")]),
    ("JOB_PREP", "technical", "Object-oriented programming: the four pillars",
     "A class is a blueprint; an object is an instance of it.\n- Encapsulation: keep data and the methods that use it together, and hide the details.\n- Inheritance: a class reuses another class.\n- Polymorphism: the same method name behaves differently for different classes.\n- Abstraction: show what something does, not how.",
     W, "Pick a real thing such as a bank account or a library book. Describe a class for it: its data, two methods, and one example of inheritance or polymorphism.",
     [("Hiding data inside a class is called:", ["Inheritance", "Encapsulation", "Polymorphism", "Compilation"], 1, "Encapsulation bundles and protects data."),
      ("A class reusing another class's features is:", ["Abstraction", "Inheritance", "Overloading", "Recursion"], 1, "The child class inherits from the parent."),
      ("The same method name doing different things in different classes is:", ["Polymorphism", "Encapsulation", "Iteration", "Indexing"], 0, "Poly means many forms."),
      ("An object is:", ["A blueprint", "An instance of a class", "A loop", "A file"], 1, "Objects are created from classes.")]),
    # ---------------- HR interview
    ("JOB_PREP", "hr", "Tell me about yourself",
     "Use a short structure of about 1 to 2 minutes:\n1. Who you are and your course.\n2. One or two skills or a project that fits the role.\n3. A strength with a small example.\n4. What you want to do next.\nDo not read your CV line by line and do not memorise a long script.",
     W, "Write your own answer to 'Tell me about yourself' in 150 to 200 words: who you are, what you studied, one project, one strength and your goal.",
     [("How long should a good answer be?", ["10 seconds", "1 to 2 minutes", "10 minutes", "30 minutes"], 1, "Short enough to hold attention, long enough to be useful."),
      ("What should it include?", ["Family details only", "Education, skills, a project and your goal", "Salary expectations", "Weaknesses only"], 1, "It should show why you suit the role."),
      ("Which is a good habit?", ["Memorise a long script word for word", "Give a short, structured answer", "Talk only about hobbies", "Say you have no weaknesses"], 1, "Structure keeps you clear and calm.")]),
    ("JOB_PREP", "hr", "Strengths and weaknesses",
     "Choose a real strength and back it with an example. For a weakness, choose a real one that is not essential for the job, and say what you are doing to improve it.\nAvoid answers like 'I work too hard' that sound rehearsed.",
     W, "Write one real strength of yours with an example, and one real weakness with what you are doing to improve it.",
     [("A good answer about a weakness:", ["Says you have none", "Names a real one and how you are improving it", "Blames a teacher", "Changes the subject"], 1, "Honesty plus improvement shows maturity."),
      ("A strength answer is stronger when it has:", ["A long list of adjectives", "A real example", "A joke", "A comparison with other students"], 1, "Examples make claims believable."),
      ("Which weakness is risky to mention for a coding job?", ["I find public speaking hard", "I cannot learn new tools", "I am shy at first", "I dislike deadlines changing"], 1, "Being unable to learn new tools is essential for the role.")]),
    # ---------------- Projects
    ("JOB_PREP", "projects", "Presenting your project in an interview",
     "Explain a project in this order: the problem it solves, the tools you used, your own role, and the result. Keep it under two minutes and be ready for 'what was the hardest part?'.\nNever claim work you did not do.",
     U, "Upload a one-page summary (PDF or Word) of your mini or final project: the problem, the tools used, your role and the result.",
     [("What should you explain first?", ["The problem the project solves", "The font you used", "Your marks", "The submission date"], 0, "Start with why the project exists."),
      ("Which detail do interviewers value most?", ["Your own role and what you learned", "How long the file name is", "The name of your guide only", "The number of pages"], 0, "They want to know what you did."),
      ("If you did only part of a team project you should:", ["Claim all of it", "Say clearly which part you did", "Avoid talking about it", "Blame the team"], 1, "Honesty builds trust.")]),
    # ---------------- Career growth
    ("CAREER", "technologies", "Choosing your first technology to learn",
     "Pick one technology at a time and build something small with it.\n- Python: scripting, data and backend.\n- SQL: the language of databases.\n- Git: tracks changes to your code.\n- HTML, CSS and JavaScript: web pages.\nLearning one thing and building with it beats starting five things.",
     W, "Pick one technology to learn this month. Write why you chose it, the first 3 topics you will study and one small thing you will build.",
     [("Which is a language for databases?", ["SQL", "HTML", "CSS", "Git"], 0, "SQL queries and manages data in databases."),
      ("Which tool tracks changes to your code?", ["Git", "SQL", "CSS", "Python"], 0, "Git is version control."),
      ("A good way to learn a technology is to:", ["Read about it for months", "Build a small project with it", "Watch videos without practice", "Learn five at once"], 1, "Practice makes it stick.")]),
    ("CAREER", "paths", "Career paths after a diploma",
     "Two common routes: join a job after the diploma, or write ECET and enter the second year of B.E./B.Tech (lateral entry) to study further. You can also do both in order: work first, then study.\nChoose by your goals, finances and interests, and keep building skills on any route.",
     W, "List two career paths you are considering after your diploma. For each, write the next three steps and the skills you still need.",
     [("What does AP ECET help diploma holders do?", ["Join B.E./B.Tech in the second year (lateral entry)", "Join an MBA", "Join a school", "Get a driving licence"], 0, "ECET is the entrance for lateral entry."),
      ("Which statement is true?", ["You must choose only one path for life", "You can work first and study later", "Skills do not matter in jobs", "Diplomas cannot be used for jobs"], 1, "Paths can be combined over time."),
      ("A good way to choose a path is:", ["Copy a friend", "Match it to your goals and skills", "Pick the shortest course", "Avoid thinking about it"], 1, "Your goals should drive the choice.")]),
    ("CAREER", "roadmap", "Stage 1: Fundamentals",
     "Build the base: programming basics (variables, loops, functions), basic data structures (lists, stacks, queues) and simple SQL.\nStudy a little every day and solve small problems.",
     W, "Write a 4-week plan for your fundamentals: what you will study each week and how you will practise.",
     [("Which belongs in the fundamentals stage?", ["Loops and functions", "Cloud architecture design", "Machine learning research", "Running a company"], 0, "Fundamentals come first."),
      ("Which data structure removes the newest item first?", ["Queue", "Stack", "Array only", "Graph"], 1, "A stack is last in, first out."),
      ("Best study habit:", ["A little every day", "Only before exams", "Only watching videos", "Skipping practice"], 0, "Regular practice builds skill.")]),
    ("CAREER", "roadmap", "Stage 2: Build projects",
     "Turn what you know into small projects: a calculator, a to-do list, a student database. Put the code on GitHub and write a short README that says what it does and how to run it.",
     U, "Upload a screenshot or a ZIP of a small project you built, with a short README explaining what it does.",
     [("What is a README?", ["A file that explains your project", "A type of database", "A programming language", "A virus"], 0, "It tells others what the project is and how to run it."),
      ("Where can you share your code publicly?", ["GitHub", "A calculator", "A spreadsheet only", "Nowhere"], 0, "GitHub hosts repositories."),
      ("Which is a good first project?", ["A to-do list app", "An operating system", "A search engine", "A game engine"], 0, "Start small and finish it.")]),
    ("CAREER", "roadmap", "Stage 3: Apply and interview",
     "Prepare a one-page résumé, polish your project explanations, and apply to many roles. Tailor your résumé to each role by moving the most relevant skills to the top.",
     W, "List 5 roles or companies you will apply to and, for each, the one skill or project you will put first in your résumé.",
     [("How long should a fresher's résumé be?", ["One page", "Ten pages", "Half a line", "No limit"], 0, "One page is the usual advice."),
      ("Tailoring a résumé means:", ["Changing it to match the role", "Making the font large", "Adding unrelated jobs", "Copying another résumé"], 0, "Put the most relevant skills first."),
      ("Before an interview you should:", ["Practise explaining your projects", "Skip sleeping", "Avoid reading the job post", "Memorise random facts"], 0, "Clear explanations help most.")]),
    ("CAREER", "projects", "Project idea: Student attendance tracker",
     "Build a small app where faculty mark attendance and students see their percentage.\n- Tables: students, subjects, attendance (student, subject, date, present).\n- Screens: login, mark attendance, my attendance.\n- Attendance % = classes attended / classes held x 100.",
     W, "Describe the tables (columns) and the three screens for an attendance tracker. Add one report you would show faculty.",
     [("Attendance % is:", ["Classes held / attended x 100", "Classes attended / classes held x 100", "Absent days x 100", "Total students x 100"], 1, "Attended divided by held."),
      ("Which table links a student to a date?", ["attendance", "subjects", "students only", "none of these"], 0, "The attendance table records who was present when."),
      ("Which column uniquely identifies a student row?", ["A primary key such as roll number", "The student's mood", "The date", "The subject name"], 0, "Primary keys identify rows.")]),
    # ---------------- Communication
    ("COMM", "spoken", "Introducing yourself",
     "A simple introduction: greeting, name, college and branch, one interest or goal, and a polite close.\nExample: 'Good morning. I am Ravi, a third-semester CSE student at ABC Polytechnic. I enjoy building small web pages and I want to become a developer. Thank you.'",
     R, "Record a 45-second introduction: your name, college, branch and one goal.",
     [("A good opening greeting in the morning is:", ["Good morning", "Hey you", "What is up", "Hello bro"], 0, "Use a polite, time-appropriate greeting."),
      ("Which detail belongs in a short introduction?", ["Name, college and goal", "Your passwords", "Your bank details", "Other people's marks"], 0, "Keep it relevant and safe."),
      ("How should you speak?", ["Clearly and not too fast", "As fast as possible", "In a whisper", "Without pauses"], 0, "Clarity beats speed.")]),
    ("COMM", "spoken", "Everyday conversations: asking for help",
     "Polite request patterns: 'Excuse me, could you help me...', 'Could you please tell me where...', 'Thank you so much for your help.'\nUse 'could' and 'would' to sound polite, and always say thank you.",
     R, "Record yourself asking a librarian for help finding a book on databases. Use at least two polite phrases.",
     [("Which is the most polite way to ask?", ["Give me the book", "Could you please help me find a book?", "Where is the book", "Find it"], 1, "'Could you please' is polite."),
      ("After someone helps you, you should say:", ["Nothing", "Thank you", "Whatever", "Okay bye"], 1, "Always thank people."),
      ("To get someone's attention politely you say:", ["Hey", "Excuse me", "Listen", "Oi"], 1, "'Excuse me' is polite.")]),
    ("COMM", "vocabulary", "Words for the workplace",
     "Useful workplace words:\n- deadline: the time by which work must be finished\n- colleague: a person you work with\n- feedback: comments on how well you did\n- schedule: a plan of when things happen\n- responsible: in charge of something",
     W, "Write five sentences about a workday using these words: deadline, colleague, feedback, schedule, responsible.",
     [("A deadline is:", ["The time work must be finished", "A kind of tool", "A break time", "A salary"], 0, "It is the latest time to finish."),
      ("A colleague is:", ["A person you work with", "A competitor shop", "A holiday", "A task"], 0, "Colleagues work together."),
      ("Feedback is:", ["Comments on your work", "A type of email", "A deadline", "A bonus"], 0, "Feedback tells you how to improve.")]),
    ("COMM", "grammar", "Present and past tense",
     "Simple present: habits and facts - 'She goes to college every day.'\nSimple past: finished actions - 'Yesterday he watched a movie.'\nPresent continuous: happening now - 'They are studying.'",
     W, "Write six sentences about your day yesterday using the past tense. Underline the verb in each sentence.",
     [("Choose the correct sentence.", ["She go to college every day.", "She goes to college every day.", "She going to college every day.", "She gone to college every day."], 1, "Add -s or -es for he, she and it in the simple present."),
      ("Yesterday he ___ a movie.", ["watch", "watches", "watched", "watching"], 2, "Past of watch is watched."),
      ("They ___ studying now.", ["is", "are", "was", "be"], 1, "'They' takes 'are'.")]),
    ("COMM", "grammar", "Articles: a, an and the",
     "Use 'a' before a consonant sound (a book) and 'an' before a vowel sound (an apple, an hour). Use 'the' for something specific that both people know about (the book on the table).",
     W, "Write a short paragraph about your college that uses a, an and the correctly at least six times.",
     [("Choose the correct article: ___ apple", ["a", "an", "the only", "no article"], 1, "'Apple' starts with a vowel sound."),
      ("Choose the correct article: ___ hour", ["a", "an", "the only", "no article"], 1, "'Hour' starts with a vowel sound because the h is silent."),
      ("Which sentence is correct?", ["I saw a elephant.", "I saw an elephant.", "I saw elephant.", "I saw the elephants a."], 1, "'An' goes before a vowel sound.")]),
    ("COMM", "speaking", "Speaking prompt: Describe your project",
     "Structure your answer: the problem, what you built, the tools, your role, and the result. Speak for about one minute.",
     R, "Record a one-minute description of a project you have done or would like to do: the problem, the tools and your role.", []),
    ("COMM", "speaking", "Speaking prompt: Why should we hire you?",
     "Give three reasons: a relevant skill, a project or example that proves it, and your willingness to learn. Stay confident and polite.",
     R, "Record a one-minute answer to 'Why should we hire you?' with three reasons.", []),
    ("COMM", "speaking", "Speaking prompt: Your career goal",
     "Say what you want to become, why, and what you are doing now to get there. Keep it honest and specific.",
     R, "Record a one-minute answer to 'Where do you see yourself in five years?'", []),
    ("COMM", "listening", "Listening for the main points",
     "Good listening: focus on the speaker, note the main points (not every word), notice keywords like 'first', 'however' and 'in conclusion', and ask a question if something is unclear.",
     W, "Listen to a 3-minute news clip or talk of your choice. Write the speaker's three main points in your own words and the name of what you listened to.",
     [("Good listeners:", ["Note the main points", "Write every word", "Look at their phone", "Interrupt often"], 0, "Main points matter more than every word."),
      ("Words like 'however' usually signal:", ["A contrast", "The end of the world", "A greeting", "A number"], 0, "'However' introduces a contrast."),
      ("If you do not understand, you should:", ["Politely ask a question", "Leave", "Pretend", "Laugh"], 0, "Clarifying is a sign of good listening.")]),
    ("COMM", "gd", "Group discussion basics",
     "Start with a short opening, make one point at a time, support it with an example, listen to others, and never shout or interrupt. Close by summarising the group's view.",
     W, "Write a 100-word opening statement for the topic 'Should mobile phones be allowed in classrooms?' with one point for and one against.",
     [("A good GD participant:", ["Listens and builds on others' points", "Interrupts everyone", "Stays silent", "Insults others"], 0, "Respectful listening wins."),
      ("A strong point includes:", ["An example", "Only a loud voice", "Personal attacks", "Random facts"], 0, "Examples make points convincing."),
      ("At the end you should:", ["Summarise the discussion", "Argue again", "Leave without speaking", "Change the topic"], 0, "A summary shows leadership.")]),
    ("COMM", "presentation", "Giving a short presentation",
     "Keep slides simple: one idea per slide, large text, and a picture or diagram where it helps. Open with the topic, give 2 or 3 key points, and close with a summary. Practise out loud.",
     U, "Upload a 3-slide outline (PDF) for a 3-minute presentation on a topic from your branch.",
     [("How many ideas should a slide carry?", ["One", "Ten", "Twenty", "As many as fit"], 0, "One idea keeps slides clear."),
      ("A good presentation ends with:", ["A summary", "An apology", "Silence", "New unrelated topic"], 0, "End by repeating the key message."),
      ("To improve delivery you should:", ["Practise out loud", "Read the slide word for word", "Avoid eye contact", "Speak quickly"], 0, "Practice builds confidence.")]),
    ("COMM", "interview", "Answering with the STAR method",
     "STAR helps you answer 'tell me about a time...' questions:\n- Situation: the context\n- Task: what you had to do\n- Action: what you did\n- Result: what happened and what you learned",
     W, "Write a STAR answer (Situation, Task, Action, Result) for: 'Tell me about a time you worked in a team.'",
     [("STAR stands for:", ["Situation, Task, Action, Result", "Skill, Talent, Attitude, Reward", "Start, Think, Act, Rest", "Speak, Talk, Argue, Relax"], 0, "It is a structure for behavioural answers."),
      ("In STAR, 'Action' is:", ["What you did", "What others did", "The outcome", "The place"], 0, "Describe your own steps."),
      ("Why add the Result?", ["It shows the outcome of your effort", "It makes the answer longer", "It is not needed", "To change topic"], 0, "Results show impact.")]),
    ("COMM", "professional", "Writing a professional email",
     "Parts of a good email: a clear subject line, a polite greeting (Dear Sir/Madam or Dear Mr/Ms Name), a short opening that states your purpose, details in one or two short paragraphs, a polite close and your full name and contact details.",
     W, "Write an email to a company asking about internship openings: subject line, greeting, three short paragraphs and a closing.",
     [("A good subject line is:", ["Clear and specific", "Empty", "ALL CAPITALS", "Very long"], 0, "A clear subject tells the reader what the email is about."),
      ("Which greeting is professional?", ["Dear Sir/Madam", "Hey", "Yo", "Hi buddy"], 0, "Use a formal greeting."),
      ("A professional email should be:", ["Short and polite", "Full of emojis", "Written in slang", "Without a closing"], 0, "Brevity and politeness matter.")]),
]

# Hands-on task per lesson where the plain written answer is not the right fit: (area, section, title) -> (type, prompt, options)
TASKS = {
    ("JOB_PREP", "hr", "Tell me about yourself"): (R, "Record a 1-minute answer to 'Tell me about yourself': your name and course, one project, one strength and your goal.", []),
    ("JOB_PREP", "hr", "Strengths and weaknesses"): ("VOICE_TEXT", "Record your answer, then write your one strength (with an example) and one weakness (with how you are improving it).", []),
    ("JOB_PREP", "coding", "Strings in Python: reverse and palindrome"): ("CODE", "Write is_palindrome(s) that ignores case and spaces. Paste your code here.", []),
    ("JOB_PREP", "coding", "Lists and loops: finding the largest number"): ("CODE", "Write code that finds the second largest number in a list without sorting it. Paste your code here.", []),
    ("JOB_PREP", "technical", "SQL basics: SELECT, WHERE and GROUP BY"): ("CODE", "Table students(id, name, branch, marks). Write SQL to (a) list names of CSE students with marks above 60 and (b) count students in each branch.", []),
    ("CAREER", "technologies", "Choosing your first technology to learn"): ("SELECT", "Which technologies do you want to learn? Choose from the list and explain why.",
        ["Python", "SQL", "HTML & CSS", "JavaScript", "React", "Django", "AI & Machine Learning", "Cloud Computing"]),
    ("CAREER", "paths", "Career paths after a diploma"): ("SELECT", "Which paths are you considering after your diploma? Choose and explain what you will do next.",
        ["Private sector job", "Government job", "AP ECET and B.E./B.Tech lateral entry", "Work first, study later", "Freelancing or own business"]),
    ("CAREER", "roadmap", "Stage 1: Fundamentals"): ("CHECKLIST", "Tick each step when you have really done it.",
        ["Learn variables, data types and operators", "Write programs with loops and functions", "Practise lists and dictionaries", "Learn basic SQL queries", "Solve 20 small practice problems"]),
    ("CAREER", "roadmap", "Stage 3: Apply and interview"): ("CHECKLIST", "Tick each step when you have really done it.",
        ["Make a one-page resume", "Prepare to explain every project", "Practise a mock interview", "Create or update your online profile", "Apply to 5 roles"]),
    ("CAREER", "projects", "Project idea: Student attendance tracker"): ("URL", "Build the tracker, put it on GitHub and share the link. In the box, write in two lines what it does.", []),
    ("COMM", "grammar", "Present and past tense"): ("WRITTEN", "Correct each sentence and write the corrected version: 1) She go to college every day. 2) Yesterday I watch a movie. 3) They is studying now. 4) He don't like tea.", []),
    ("COMM", "gd", "Group discussion basics"): ("VOICE_TEXT", "Topic: 'Should mobile phones be allowed in classrooms?' Record a 1-minute opinion, then write your two main points.", []),
    ("COMM", "presentation", "Giving a short presentation"): ("UPLOAD", "Upload a short video or audio (MP4, WEBM, MP3 or M4A, up to 25 MB) of you presenting a topic from your branch, or a PDF of your 3 slides.", []),
    ("COMM", "interview", "Answering with the STAR method"): (R, "Record a 1-minute STAR answer: 'Tell me about a time you worked in a team.'", []),
}


class Command(BaseCommand):
    help = "Add lessons with topic practice questions and hands-on tasks (Job preparation, Career growth, Communication)."

    def handle(self, *args, **opts):
        tracking.SILENT = True  # loading lessons in bulk should not notify students
        try:
            self._run()
        finally:
            tracking.SILENT = False

    def _run(self):
        admin = User.objects.filter(role=Role.ADMIN, is_active=True).order_by("id").first()
        made = skipped = qn = 0
        for order, (area, section, title, body, task_type, prompt, questions) in enumerate(LESSONS):
            existing = Guide.objects.filter(area=area, section=section, title=title).first()
            if existing:
                if (area, section, title) in TASKS:
                    t, pr, op = TASKS[(area, section, title)]
                    GuideTaskSetting.objects.update_or_create(guide=existing, defaults={"task_type": t, "prompt": pr, "options": op})
                skipped += 1
                continue
            g = Guide.objects.create(area=area, section=section, kind="NOTES", title=title, body=body, order_no=order, uploaded_by=admin)
            task_type, prompt, task_opts = TASKS.get((area, section, title), (task_type, prompt, []))
            GuideTaskSetting.objects.create(guide=g, task_type=task_type, prompt=prompt, options=task_opts)
            for i, (text, opts_, correct, why) in enumerate(questions):
                GuideQuestion.objects.create(guide=g, text=text, option_a=opts_[0], option_b=opts_[1], option_c=opts_[2], option_d=opts_[3],
                                             correct=correct, explanation=why, order_no=i)
                qn += 1
            made += 1
        self.stdout.write(self.style.SUCCESS(f"Done. Added {made} lessons and {qn} practice questions; {skipped} already existed (their tasks were refreshed)."))
