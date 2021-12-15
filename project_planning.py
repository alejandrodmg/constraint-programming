#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ortools.sat.python import cp_model
import pandas as pd
import os

class ProjectPlanning():

    def __init__(self):
        # Create a CP Model.
        self.model = cp_model.CpModel()
        # Create a solver.
        self.solver = cp_model.CpSolver()

    def import_data(self):

        """ A) Import data:

        A.1 -> Load the excel file data.xlsx and
        extract all relevant information.
        """

        # Import data.
        data = pd.read_excel("data/data.xlsx", sheet_name=None, index_col=0)
        projects = data['Projects']
        quotes = data['Quotes']
        dependencies = data['Dependencies']
        value = data['Value']

        # Create a DataFrame stored in stacked format (tabular dataset).
        project_plan = pd.DataFrame({"Contractor": pd.Series([], dtype='int'),
                                     "Job": pd.Series([], dtype='int'),
                                     "Project": pd.Series([], dtype='int'),
                                     "Month": pd.Series([], dtype='int'),
                                     "Quote": pd.Series([], dtype='float')})

        # For each contractor:
        for c in range(len(quotes)):
            # Get the indices of the jobs that the candidate qualifies for.
            qualified_jobs = [i for i, x in \
                enumerate(quotes.iloc[c].notnull()) if x]
            # For each job:
            for j in qualified_jobs:
                # For each project:
                for p in range(len(projects)):
                    # Store the indices of the month or months a specific job will
                    # be required in a specific project.
                    running_month = [i for i, x in \
                        enumerate(projects.iloc[p] == quotes.iloc[c].index[j]) if x]
                    # If the contractors' job is needed at any point in time in this
                    # project, then store it:
                    if running_month:
                        for m in running_month:
                            project_plan = project_plan.append([{'Contractor': c,
                                                                'Job': j,
                                                                'Project': p,
                                                                'Month': m,
                                                                'Quote': quotes.iloc[c][j]}],
                                                            ignore_index=True)

        return projects, quotes, dependencies, value, project_plan

    def identify_and_create_variables(self, project_plan, projects):

        """ B) Decision variables:

        B.1 -> Identify and create the decision variables in a CP-SAT model
        that you need to decide what projects to take on.

        B.2 -> Also identify and create the decision variables you need to decide,
        which contractor is working on which project and when.
        Make sure to consider that not all contractors are qualified
        to work on all jobs and that projects do not run over
        all months.
        """

        # B.1 What projects to take on:
        var_projects = []
        # For each project:
        for p in range(len(projects)):
            # Create as many boolean variables (0, 1) as projects to take on.
            var_projects.append(self.model.NewBoolVar("p_%s"%(p)))

        # B.2 Which contractor is working on which project and when.
        # As we have already created a DataFrame with every single
        # valid combination of Contractor/Job/Project/Month, we
        # simply create a dictionary of Boolean variables with tuples
        # as keys:
        # (Contractor, Job, Project, Month) : BoolVar
        var_hiring = {}
        for row in range(len(project_plan)):
            var_hiring[tuple(project_plan.iloc[row][:-1].astype(int))] = \
                self.model.NewBoolVar("h_%s_%s_%s_%s"%(
                    project_plan.iloc[row]['Contractor'].astype(int),
                    project_plan.iloc[row]['Job'].astype(int),
                    project_plan.iloc[row]['Project'].astype(int),
                    project_plan.iloc[row]['Month'].astype(int)))

        return var_projects, var_hiring

    def define_and_implement_constraints(self, project_plan, projects, quotes, \
                                        dependencies, value, var_hiring, var_projects):

        """ C) Constraints of the model:

        C.1 -> Define and implement the constraint that a contractor
        cannot work on two projects simultaneously.

        C.2 -> Define and implement the constraint that if a project
        is accepted to be delivered then exactly one contractor
        per job of the project needs to work on it.

        C.3 -> Define and implement the constraint that if a project
        is not taken on then no one should be contracted to work on it.

        C.4 -> Define and implement the project dependency constraints.

        C.5 -> Define and implement the constraint that the profit margin, i.e. the difference
        between the value of all delivered projects and the cost of all required
        subcontractors, is at least €2500.
        """

        # C.1:
        max_n_projects = 1
        # For each contractor:
        for c in range(len(quotes)):
            # Store the months that could be potentially employed for a project.
            candidate_months = project_plan[project_plan['Contractor'] == c].Month.unique()
            # For each candidate month:
            for m in candidate_months:
                query = project_plan[(project_plan['Contractor'] == c) & (project_plan['Month'] == m)]
                # If there's a month that could be working on multiple projects:
                if len(query) > max_n_projects:
                    # Add a constrain to make sure that the sum of boolean variables for that
                    # contractor and that month is lower or equal than 1 - i.e. the contractor only
                    # works on one project per month maximum.
                    self.model.Add(sum([var_hiring[(query.iloc[i]['Contractor'], query.iloc[i]['Job'],
                                                    query.iloc[i]['Project'], query.iloc[i]['Month'])] \
                                       for i in range(len(query))]) <= max_n_projects)

        # C.2:
        max_n_contractors = 1
        # For each project:
        for p in range(len(projects)):
            # Store the months that the project could potentially be run for.
            candidate_months = project_plan[project_plan['Project'] == p].Month.unique()
            # For each candidate month:
            for m in candidate_months:
                query = project_plan[(project_plan['Project'] == p) & (project_plan['Month'] == m)]
                # If there are multiple contractors that are eligible for the job:
                if len(query) > max_n_contractors:
                    # Add a constrain that only one can work on that specific project,
                    # month, and job if and only if the project is accepted to be delivered.
                    self.model.Add(sum([var_hiring[(query.iloc[i]['Contractor'], query.iloc[i]['Job'],
                                                    query.iloc[i]['Project'], query.iloc[i]['Month'])] \
                                        for i in range(len(query))]) == max_n_contractors).\
                                            OnlyEnforceIf(var_projects[p])

        # C.3:
        # For each project:
        for p in range(len(projects)):
            query = project_plan[project_plan['Project'] == p]
            # The sum of all Boolean variables must be equal to zero if the project
            # is not taken on, i.e. no one should be contracted to work on the project.
            self.model.Add(sum([var_hiring[(query.iloc[i]['Contractor'], query.iloc[i]['Job'],
                                            query.iloc[i]['Project'], query.iloc[i]['Month'])] \
                                for i in range(len(query))]) == 0).\
                                    OnlyEnforceIf(var_projects[p].Not())

        # C.4:
        # For each project:
        for p in range(len(dependencies)):
            # Get the indices of the projects that are a dependency.
            project_dependencies = [i for i, x in \
                enumerate(dependencies.iloc[p].notnull()) if x]
            # If there's a dependency:
            if project_dependencies:
                for d in project_dependencies:
                    # Add a constrain that the project can only be delivered if the
                    # dependicy is taken on too.
                    self.model.AddBoolAnd([var_projects[d]]).OnlyEnforceIf(var_projects[p])

        # C.5:
        # Calculate revenue as the sum of all projects' value being delivered.
        revenue = sum([value.iloc[p][0].astype(int) * var_projects[p] \
                            for p in range(len(value))])
        # Calculate costs as the sum of the contractors' quotes when hired to work
        # on a specific project, month and job.
        costs = sum([var_hiring[tuple(project_plan.iloc[c][:-1].astype(int))] * \
                     project_plan.iloc[c][-1].astype(int) \
                         for c in range(len(project_plan))])
        # Add the profit margin constrain.
        self.model.Add((revenue - costs) >= 2500)

        return revenue, costs

    def solve(self):

        """ D) Solve the problem.

        D.1 - > Solve the CP-SAT model and determine how many possible
        solutions satisfy all the constraints.

        D.2 -> For each solution, determine what projects are taken on,

        D.3 -> which contractors work on which projects in which month,

        D.4 -> and what is the profit margin.
        """

        # Step 1: Import the data.
        projects, quotes, dependencies, value, project_plan = self.import_data()

        # Step 2: Create decision variables.
        var_projects, var_hiring = self.identify_and_create_variables(project_plan, projects)

        # Step 3: Implement constraints of the model.
        self.define_and_implement_constraints(project_plan, projects, quotes, \
            dependencies, value, var_hiring, var_projects)

        # Step 4: Create a solution printer (D.1, D.2, D.3, D.4 are implemented
        # in the printer class).
        sol_printer = SolutionPrinter(var_projects, var_hiring, project_plan, \
            value, projects, quotes)

        # Step 5: Search for all solutions and solve the problem.
        print('Searching for all solutions...')
        status = self.solver.SearchForAllSolutions(self.model, sol_printer)
        status_name = self.solver.StatusName(status)
        print('Optimisation finished, solver status: {}.'.format(status_name))
        print('Total time elapsed (seconds): {}'.format(round(self.solver.WallTime(), 2)))
        print('Total number of solutions found: {}'.format(sol_printer.SolutionCount()))

class SolutionPrinter(cp_model.CpSolverSolutionCallback):

    """ This class is responsible for showing in the screen the
    solutions found for this specific problem.

    We determine how many possible solutions satisfy all the
    constraints, and for each solution the projects are taken on,
    which contractors work on which projects in which month,
    and what is the profit margin.
    """

    def __init__(self, var_projects, var_hiring, project_plan,\
                 value, projects, quotes):
        cp_model.CpSolverSolutionCallback.__init__(self)
        # Decision variables.
        self.var_projects = var_projects
        self.var_hiring = var_hiring
        # DataFrame of the project plan.
        self.project_plan = project_plan
        # Variable names.
        self.value_ = value
        self.projects = projects.index.values
        self.months = projects.columns.values
        self.contractors = quotes.index.values
        # Colution counter.
        self.n_solutions = 0

    def OnSolutionCallback(self):

        # Create an empty DataFrame that will be filled with the contractors
        # needed to work on the projects that are taken on, as well as the months
        # that will be employed and their quota.
        project_solution = pd.DataFrame({"Contractor": pd.Series([], dtype='int'),
                                         "Job": pd.Series([], dtype='int'),
                                         "Project": pd.Series([], dtype='int'),
                                         "Month": pd.Series([], dtype='int'),
                                         "Quote": pd.Series([], dtype='float')})

        # Re-calculate revenue and cost for the solution found in the same
        # way that was calculted before to add the profit margin constrain.
        revenue = sum([self.value_.iloc[p][0].astype(int) * \
                                 self.Value(self.var_projects[p]) \
                                     for p in range(len(self.value_))])
        costs = sum([self.Value(self.var_hiring[tuple(self.project_plan.iloc[c][:-1].astype(int))]) * \
                               self.project_plan.iloc[c][-1].astype(int) \
                                   for c in range(len(self.project_plan))])

        # For each decision variable in the form of (Contractor, Job, Project, Month):
        for c in range(len(self.project_plan)):
            # If the variable has a True assignation:
            if self.Value(self.var_hiring[tuple(self.project_plan.iloc[c][:-1].astype(int))]):
                # Store it in the DataFrame.
                project_solution = project_solution.append(self.project_plan.iloc[c], ignore_index=True)

        # Increase the number of solutions by 1 and print the results.
        self.n_solutions += 1
        print("Feasible solution #{}".format(self.n_solutions))
        print('*'*20)
        # Get the projects that have been decided to take on.
        projects_to_take_on = [self.projects[int(p)] for p in project_solution['Project'].unique()]
        projects_to_take_on.sort()
        print('Projects that are taken on: ', str(projects_to_take_on).strip('[]'))
        print('-'*45)
        # For each contractor:
        for c in project_solution['Contractor'].unique():
            # For each project that will be working on:
            for p in project_solution[(project_solution['Contractor'] == c)]['Project'].unique():
                # For each month that will be hired for:
                for m in project_solution[(project_solution['Contractor'] == c) & \
                                          (project_solution['Project'] == p)]['Month'].unique():
                    # Print which contractors work on which projects and in which month.
                    print(self.contractors[int(c)], 'will work on', self.projects[int(p)], 'during', self.months[int(m)])

        # Print revenue, costs and profit margin.
        print('-'*45)
        print('Revenue:', revenue)
        print('Costs:', costs)
        print('Profit margin:', revenue - costs)
        print('='*45)

    def SolutionCount(self):
        return self.n_solutions


if __name__ == "__main__":

    os.system('cls' if os.name == 'nt' else 'clear')
    project_planning = ProjectPlanning()
    project_planning.solve()
