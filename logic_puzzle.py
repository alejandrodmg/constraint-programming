#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ortools.sat.python import cp_model
import pandas as pd
import os

class LogicPuzzle():

    def __init__(self):
        # Create a CP Model.
        self.model = cp_model.CpModel()
        # Create a solver.
        self.solver = cp_model.CpSolver()

    def objects_attributes_predicates(self):

        """ A) Objects, attributes and predicates.

        A.1 -> Identify the objects, attributes and predicates
        for the puzzle and create the decision variables
        in a CP-SAT model.
        """

        # There are three predicates: Nationality, University and Course.
        # They all operate on the same object domain: Student.

        # Object domain
        students = ['Carol', 'Elisa', 'Oliver', 'Lucas']

        # Atribute domain for Nationality is:
        nationalities = ['USA', 'Canada', 'Australia', 'South Africa']
        # Add 4x4 matrix of Boolean variables corresponding to all
        # combinations of objects and attributes.
        student_nationality = {}
        for student in students:
            variables = {}
            for nationality in nationalities:
                variables[nationality] = self.model.NewBoolVar(student+nationality)
            student_nationality[student] = variables

        # Atribute domain for University is:
        universities = ['London', 'Oxford', 'Cambridge', 'Edinburgh']
        # Add 4x4 matrix of Boolean variables corresponding to all
        # combinations of objects and attributes.
        student_university = {}
        for student in students:
            variables = {}
            for university in universities:
                variables[university] = self.model.NewBoolVar(student+university)
            student_university[student] = variables

        # Atribute domain for Course is:
        courses = ['History', 'Medicine', 'Law', 'Architecture']
        # Add 4x4 matrix of Boolean variables corresponding to all
        # combinations of objects and attributes.
        student_course = {}
        for student in students:
            variables = {}
            for course in courses:
                variables[course] = self.model.NewBoolVar(student+course)
            student_course[student] = variables

        # Return the object domain, predicates and decision variables.
        return students, nationalities, universities, courses, \
               student_nationality, student_university, student_course

    def add_explicit_constraints(self, students, student_nationality, \
                                    student_university, student_course):
        """ B) Explicit constraints.

        B.1 -> For each of the seven sentences in the puzzle define
        the explicit constraints contained in the sentences
        and add them to the CP-SAT model.
        Identify clearly, which sentence you are referring to.
        """

        # (1) One of them is going to London.
        self.model.Add(sum([student_university[student]['London'] for student in students]) == 1)

        # (2) Exactly one boy and one girl chose a university in a
        # city with the same initial of their names.
        self.model.Add(sum([student_university['Carol']['Cambridge'], student_university['Elisa']['Edinburgh']]) == 1)
        self.model.Add(sum([student_university['Oliver']['Oxford'], student_university['Lucas']['London']]) == 1)

        # (3) A boy is from Australia, the other studies History.
        self.model.AddBoolAnd([student_nationality['Oliver']['Australia'], student_course['Lucas']['History']]).\
            OnlyEnforceIf(student_course['Oliver']['History'].Not())
        self.model.AddBoolAnd([student_nationality['Lucas']['Australia'], student_course['Oliver']['History']]).\
            OnlyEnforceIf(student_course['Lucas']['History'].Not())

        # (4) A girl goes to Cambridge, the other studies Medicine.
        self.model.AddBoolAnd([student_university['Carol']['Cambridge'], student_course['Elisa']['Medicine']]).\
            OnlyEnforceIf(student_course['Carol']['Medicine'].Not())
        self.model.AddBoolAnd([student_university['Elisa']['Cambridge'], student_course['Carol']['Medicine']]).\
            OnlyEnforceIf(student_course['Elisa']['Medicine'].Not())

        # (5) Oliver studies Law or is from USA; He is not from South Africa.
        self.model.AddBoolOr([student_nationality['Oliver']['USA'], student_course['Oliver']['Law']])
        self.model.AddBoolAnd([student_nationality['Oliver']['South Africa'].Not()])

        # (6) The student from Canada is a historian or will go to Oxford.
        for student in students:
            self.model.AddBoolOr([student_course[student]['History'], student_university[student]['Oxford']]).\
                OnlyEnforceIf(student_nationality[student]['Canada'])

        # (7) The student from South Africa is going to Edinburgh or will study Law.
        for student in students:
            self.model.AddBoolOr([student_course[student]['Law'], student_university[student]['Edinburgh']]).\
                OnlyEnforceIf(student_nationality[student]['South Africa'])

    def add_implicit_constraints(self, students, nationalities, universities, courses,\
                                student_nationality, student_university, student_course):

        """ C) Implicit constraints.

        C.1 -> The puzzle also contains some implicit constraints.
        Define and implement these implicit constraints in
        the CP-SAT model.
        """

        # (1) Each student has exactly one nationality.
        for nationality in nationalities:
            self.model.Add(sum([student_nationality[student][nationality] for student in students]) == 1)

        # (2) Each student goes to exactly one university.
        for university in universities:
            self.model.Add(sum([student_university[student][university] for student in students]) == 1)

        # (3) Each student studies exactly one course.
        for course in courses:
            self.model.Add(sum([student_course[student][course] for student in students]) == 1)

        # (4) Each nationality, university and course can be picked exactly once.
        for student in students:
            self.model.Add(sum([student_nationality[student][nationality] for nationality in nationalities]) == 1)
            self.model.Add(sum([student_university[student][university] for university in universities]) == 1)
            self.model.Add(sum([student_course[student][course] for course in courses]) == 1)

    def solve(self):

        """ D) Solve the problem.

        D.1 -> Solve the CP-SAT model and determine for each student
        the nationality, the university and the course they chose.
        """

        # Step 1: Define and implement objects, attributes and predicates.
        students, nationalities, universities, courses, \
            student_nationality, student_university, student_course = self.objects_attributes_predicates()

        # Step 2: Define and implement explicit constraints.
        self.add_explicit_constraints(students, student_nationality, student_university, student_course)

        # Step 3: Define and implement implicit constraints.
        self.add_implicit_constraints(students, nationalities, universities, courses,\
            student_nationality, student_university, student_course)

        # Step 4: Create a solution printer (subtask D is implemented in the printer class).
        sol_printer = SolutionPrinter(students, nationalities, universities, courses, \
                        student_nationality, student_university, student_course)

        # Step 5: Solve the problem and search for all solutions.
        print('Searching for all solutions...')
        status = self.solver.SearchForAllSolutions(self.model, sol_printer)
        status_name = self.solver.StatusName(status)
        print('Optimisation finished, solver status: {}.'.format(status_name))
        print('Total time elapsed (seconds): {}'.format(round(self.solver.WallTime(), 2)))
        print('Total number of solutions found: {}'.format(sol_printer.SolutionCount()))

class SolutionPrinter(cp_model.CpSolverSolutionCallback):

    """ This class is responsible for showing in the screen the solutions
    found for this specific problem.

    We determine for each student the nationality, the university and
    the course they chose.
    """

    def __init__(self, students, nationalities, universities, courses, \
                 student_nationality, student_university, student_course):
        cp_model.CpSolverSolutionCallback.__init__(self)
        # Variables.
        self.student_nationality = student_nationality
        self.student_university = student_university
        self.student_course = student_course
        # Variables values.
        self.students = students
        self.nationalities = nationalities
        self.universities = universities
        self.courses = courses
        # Solution counter.
        self.n_solutions = 0

    def OnSolutionCallback(self):

        # Create an empty DataFrame that will be filled with the results
        # where each row corresponds to a student.
        puzzle_solution = pd.DataFrame({"Student": pd.Series([], dtype='str'),
                                       "Nationality": pd.Series([], dtype='str'),
                                       "University": pd.Series([], dtype='str'),
                                       "Course": pd.Series([], dtype='str')})
        # For each student:
        for student in self.students:
            # Find the True assignation for each predicate:
            for nationality in self.nationalities:
                if self.Value(self.student_nationality[student][nationality]):
                    break
            for university in self.universities:
                if self.Value(self.student_university[student][university]):
                    break
            for course in self.courses:
                if self.Value(self.student_course[student][course]):
                    break
            # Append the results to the DataFrame.
            puzzle_solution = puzzle_solution.append({'Student': student,
                                                      'Nationality': nationality,
                                                      'University': university,
                                                      'Course': course},
                                                      ignore_index=True)
        # Increase the number of solutions by 1 and print the results.
        self.n_solutions += 1
        print("Feasible solution #{}".format(self.n_solutions))
        print('*'*20)
        print(puzzle_solution.to_string())
        print('='*48)

    def SolutionCount(self):
        return self.n_solutions

if __name__ == "__main__":

    os.system('cls' if os.name == 'nt' else 'clear')
    logic_puzzle = LogicPuzzle()
    logic_puzzle.solve()
