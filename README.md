
## Example 1: Logic Puzzle

A constraint satisfaction model that solves the following logical puzzle:

```
Carol, Elisa, Oliver and Lucas are going to university.
One of them is going to London (1).
Exactly one boy and one girl chose a university in a city with the same initial of their names (2).
A boy is from Australia, the other studies History (3).
A girl goes to Cambridge, the other studies Medicine (4).
Oliver studies Law or is from USA; He is not from South Africa (5).
The student from Canada is a historian or will go to Oxford (6).
The student from South Africa is going to Edinburgh or will study Law (7).
```

**What is the nationality of the architecture student?**

Steps:

- Identify the objects, attributes and predicates for the puzzle and create the decision variables in a CP-SAT model.
- For each of the seven sentences in the puzzle define the explicit constraints contained in the sentences and add them to the CP-SAT model. 
- Identify clearly, which sentence you are referring to.
- The puzzle also contains some implicit constraints. Define and implement these implicit constraints in the CP-SAT model.
- Solve the CP-SAT model and determine for each student the nationality, the university and the course they chose.
- Evaluate for each of the seven sentences in the puzzle if they are redundant. Which sentences can be omitted from the puzzle and why? 

## Example 2: Project Planning

A constraint satisfaction problem model for deciding what projects can be taken on and what companies need to be contracted to deliver on these projects. 

- In the **Projects** sheet you will find a list of projects, for each projects the jobs that need to be carried out and the months this needs to happen (e.g. Project E required Job J in month M8 and Job A in month M9).
- In the **Quotes** sheet you will find a list of contractors and their quotes for each of the jobs they are qualified to carry out (e.g. Contractor A charges €230 for Job A). A contractor can only work in one project at a time.
- In the **Dependencies** sheet you will find a matrix of project dependencies indicating which projects are pre-requisites for the delivery of other projects (e.g. Project B can only be taken on, if also Project A is taken on).
- In the **Value** sheet you will find the value of each project (e.g. Project A is worth €500).

The goal is to determine which projects can be delivered and what subcontractors should be contracted while making sure that the overall profit margin is at least €2500.

- Load the excel file data.xlsx and extract all relevant information. Make sure to use the data from the file in your code, please do not hardcode any values that can be read from the file.
- Identify and create the decision variables in a CP-SAT model that you need to decide what projects to take on. Also identify and create the decision variables you need to decide, which contractor is working on which project and when. Make sure to consider that not all contractors are qualified to work on all jobs and that projects do not run over all months.
- Define and implement the constraint that a contractor cannot work on two projects simultaneously.
- Define and implement the constraint that if a project is accepted to be delivered then exactly one contractor per job of the project needs to work on it.
- Define and implement the constraint that if a project is not taken on then no one should be contracted to work on it.
- Define and implement the project dependency constraints.
- Define and implement the constraint that the profit margin, i.e. the difference
between the value of all delivered projects and the cost of all required
subcontractors, is at least €2500.
- Solve the CP-SAT model and determine how many possible solutions satisfy all the
constraints. For each solution, determine what projects are taken on, which contractors work on which projects in which month, and what is the profit margin.