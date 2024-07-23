import pulp
import pandas as pd
from pandas.tseries.offsets import MonthBegin
import logging
import os
import yaml

def save_results(results_df):
    """
    Saves the results to a CSV file in the 'results' directory with an incremented filename.

    Parameters:
    results_df (DataFrame): The dataframe containing the results to save.
    """
    # Ensure the results directory exists
    if not os.path.exists('results'):
        os.makedirs('results')
    
    # Determine the next available filename
    i = 1
    while os.path.exists(f'results/results{i}.csv'):
        i += 1
    
    # Save the results to the next available filename
    results_df.to_csv(f'results/results{i}.csv', index=False)
    logging.info(f'Results saved to results/results{i}.csv')
    
def data_preparation(buildings_df):
    """
    Prepares and returns data related to building information used by the optimization procedure.

    Parameters:
    buildings_df (int): Uses a dataframe as an input. It should include the columns:
    'Pandcode', 'Rent (Monthly)', 'Contractdue (Months)', 'Occupation (Max)', 'Neighbors', 'Desks'

    Return:
    DataFrame: A dataframe containing information for each building.
    Each row includes a unique id, monthly cost, contract ending date, 
    number of workers, neighboring buildings and building capacity
    Dictionary: A dictionary containing information for each building. 
    Each entry includes a unique id, monthly cost, contract ending date, 
    number of workers, neighboring buildings and building capacity
    """
    
    logging.info("Preparing the data")
    
    required_columns = ['Pandcode', 'Rent (Monthly)', 'Contractdue (Months)', 'Occupation (Max)', 'Neighbors', 'Desks']
    
    # Check if all required columns are present in the dataframe
    missing_columns = [col for col in required_columns if col not in buildings_df.columns]
    if missing_columns:
        logging.error(f"Missing columns in the dataframe: {missing_columns}")
        return None, None
    
    logging.info("All required columns are present. Preparing the data.")

    # Make from the dataframe a list of dictionaries
    try:
        buildings = buildings_df.astype({'Pandcode': 'str',
                                        'Rent (Monthly)': 'int64',
                                        'Contractdue (Months)': 'int64',
                                        'Occupation (Max)': 'int64',
                                        'Neighbors': 'str',
                                        'Desks': 'int64'})
        logging.info('Columns have been transformed into the correct format')
    except:
        logging.error('Unable to transform the columns in the correct format. Check the examples for the correct formatting.')

    buildings = buildings_df.to_dict('records')
    
    logging.info("Data preparation is complete.")

    return buildings_df, buildings

def pand_optimizer(pand_dictionary, periods = 100):
    """
    Finds an optimal solution for worker allocation accross buildings with hybrid work environments.

    Parameters:
    pand_dictionary (dict): A dictionary containing information for each building. 
    Each entry includes a unique id, monthly cost, contract ending date, 
    number of workers, neighboring buildings and building capacity

    Return:
    x (LpVariable): The optimized variable in pulp which is equal to 1 when a building is open 
    in a given month and 0 if it is closed.
    y (LpVariable): The optimized variable in pulp which is equal to 1 when workers are moved to a neighboring building
    and 0 if they are not moved.
    """

    logging.info("Optimizing...")
    # Create an LP problem instance
    prob = pulp.LpProblem("Building_Closure_Optimization", pulp.LpMinimize)

    # Decision variables x: which is open or closed (1, 0), y: moved workers which is moved or not moved: (1,0), and z: moving workers which is moving or not moving (1,0)
    x = pulp.LpVariable.dicts("x", [(i["Pandcode"], j) for i in pand_dictionary for j in range(1, periods)], cat='Binary')
    y = pulp.LpVariable.dicts("y", [(i["Pandcode"], j, k["Pandcode"]) for i in pand_dictionary for j in range(1, periods) for k in pand_dictionary if k["Pandcode"] in i["Neighbors"]], cat='Binary')
    z = pulp.LpVariable.dicts("z", [(i["Pandcode"], j, k["Pandcode"]) for i in pand_dictionary for j in range(1, periods) for k in pand_dictionary if k["Pandcode"] in i["Neighbors"]], cat='Binary')
    # Objective function
    moving_cost = 0
    prob += (
        pulp.lpSum(i["Rent (Monthly)"] * x[i["Pandcode"], j] for i in pand_dictionary for j in range(1, periods)) + 
        pulp.lpSum(moving_cost * k["Occupation (Max)"] * z[i["Pandcode"], j, k["Pandcode"]]
                   for i in pand_dictionary
                   for j in range(1, periods)
                   for k in pand_dictionary if k["Pandcode"] in i["Neighbors"])
    )
    # Constraints
    
    # Constraint 1
    for i in pand_dictionary:
        if i["Contractdue (Months)"] > (periods -1):
            for j in range(1, periods):
                prob += x[i["Pandcode"], j] == 1
        else:
            for j in range(1, i["Contractdue (Months)"] + 1):
                prob += x[i["Pandcode"], j] == 1

    # Constraint 2
    for i in pand_dictionary:
        for j in range(1, periods):
            prob += i["Occupation (Max)"] * x[i["Pandcode"], j] + pulp.lpSum(k["Occupation (Max)"] * y[k["Pandcode"], j, i["Pandcode"]] for k in pand_dictionary if k["Pandcode"] in i["Neighbors"]) <= i["Desks"]
    
    # Constraint 3
    for i in pand_dictionary:
        for j in range(1, periods):
            prob += pulp.lpSum(y[i["Pandcode"], j, k["Pandcode"]] for k in pand_dictionary if k["Pandcode"] in i["Neighbors"]) <= 1
    
    # Constraint 4
    for i in pand_dictionary:
        for j in range(1, periods):
            for k in pand_dictionary:
                if k["Pandcode"] in i["Neighbors"]:
                    prob += x[i["Pandcode"], j] >= y[k["Pandcode"], j, i["Pandcode"]]
    
    # Constraint 5
    for i in pand_dictionary:
        for j in range(1, periods):
            prob += x[i["Pandcode"], j] + pulp.lpSum(y[i["Pandcode"], j, k["Pandcode"]] for k in pand_dictionary if k["Pandcode"] in i["Neighbors"]) == 1
    
    # Constraint 6
    for i in pand_dictionary:
        for j in range(1, (periods - 1)):  # Up to 36 because j+1 will be 37
            prob += x[i["Pandcode"], j] >= x[i["Pandcode"], j + 1]

    # Constraint 7: Ensuring that the moving variable is only 1 when y changes from 0 to 1.
    for i in pand_dictionary:
        for j in range(1,periods):
            for k in pand_dictionary:
                if k["Pandcode"] in i["Neighbors"]:
                    if j == 1:
                        prob += z[i["Pandcode"], j, k["Pandcode"]] == y[i["Pandcode"], j, k["Pandcode"]]
                    else:
                        prob += z[i["Pandcode"], j, k["Pandcode"]] >= y[i["Pandcode"], j, k["Pandcode"]] - y[i["Pandcode"], j-1, k["Pandcode"]]
                        prob += z[i["Pandcode"], j, k["Pandcode"]] <= y[i["Pandcode"], j, k["Pandcode"]]
                        prob += z[i["Pandcode"], j, k["Pandcode"]] <= 1 - y[i["Pandcode"], j-1, k["Pandcode"]]

    # Solve the problem
    status = prob.solve(PULP_CBC_CMD(msg=0))
                    
    if pulp.LpStatus[status] == 'Optimal':
        logging.info("Found an optimal solution.")
    else:
        logging.warning("Could not find an optimal solution.")
        logging.warning("Continuing with the unoptimal output.")
    return x, y

def optimizer_to_dataframe(buildings_df, pand_dictionary, x, y, periods):
    """
    Transforms the solution to the optimization problem into a readable dataframe.

    Parameters:
    pand_dictionary (dict): A dictionary containing information for each building. 
    Each entry includes a unique id, monthly cost, contract ending date, 
    number of workers, neighboring buildings and building capacity
    buildings_df (DataFrame): A dataframe containing information for each building.
    Each row includes a unique id, monthly cost, contract ending date, 
    number of workers, neighboring buildings and building capacity
    x (LpVariable): The optimized variable in pulp which is equal to 1 when a building is open 
    in a given month and 0 if it is closed.
    y (LpVariable): The optimized variable in pulp which is equal to 1 when workers are moved to a neighboring building
    and 0 if they are not moved.    

    Return:
    df (DataFrame): A dataframe with the optimal solution and the corresponding information.
    """
    
    logging.info("Preparing the optimized data")
    # Results

    df = pd.DataFrame(columns = ['Pandcode', 'Month', 'Status', 'pandcode_real'])
    # Extracting names and values for x and y   
    for i in pand_dictionary:
        Pandcode = i['Pandcode']
        for j in range(1, periods):
            Ysum = 0
            for k in pand_dictionary:
                if k["Pandcode"] in i["Neighbors"] and y[i["Pandcode"], j, k["Pandcode"]].varValue == 1:
                    Reallocatie_pandcode = k['Pandcode']
                    Ysum += 1
            if Ysum == 0:
                Reallocatie_pandcode = Pandcode              
            month = j
            if x[i["Pandcode"], j].varValue == 1:
                status = 'Open'
            else:
                status = 'Closed'

            df.loc[len(df.index)] = [Pandcode, month, status, Reallocatie_pandcode]
    
    df = df.merge(buildings_df, left_on = 'Pandcode' , right_on = ['Pandcode'], how = 'left')
    
    reallocatie_df = buildings_df
    reallocatie_df.columns = ['pandcode_real', 'kosten_real', 'end_date_real', 'workers_real', 'neighbors_real', 'capacity_real']
    
    df = df.merge(reallocatie_df, on = 'pandcode_real', how = 'left')

    today = pd.to_datetime("today")
    first_of_next_month = today + MonthBegin(1)
    df["DatumID"] = df["Month"].apply(lambda x: (first_of_next_month + pd.DateOffset(months=x)).replace(day=1).date())
    df = df.drop(['Neighbors', 'neighbors_real'], axis = 1)
    return df

def load_config(config_file='config.yaml'):
    try:
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
        logging.info("Configuration loaded successfully.")
        return config
    except Exception as e:
        logging.error(f"Failed to load configuration file: {e}")
        return None