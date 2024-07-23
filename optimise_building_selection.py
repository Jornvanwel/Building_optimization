import pulp
import pandas as pd
from datetime import date, timedelta
import math
from pandas.tseries.offsets import MonthBegin
from pandas.tseries.offsets import MonthBegin

def distance_calculator(lat1, lon1, lat2, lon2):
    """
    Calculates the distance between two locations.

    Parameters:
    lat1 (float): The latitude of the first location.
    lon1 (float): The longitude of the first location.
    lat2 (float): The latitude of the second location.
    lon2 (float): The longitude of the second location.

    Return:
    float: The distance between the two location in km's.
    """
    r = 6371 # km
    p = math.pi / 180

    a = 0.5 - math.cos((lat2-lat1)*p)/2 + math.cos(lat1*p) * math.cos(lat2*p) * (1-math.cos((lon2-lon1)*p))/2
    return 2 * r * math.asin(math.sqrt(a))

def add_month_diff(df):
    """
    Adds a column with the difference between today and the ending date of the contract column.

    Parameters:
    df (DataFrame): A dataframe with buildings and the ending date of the contract.

    Return:
    DataFrame: A dataframe with the new 'end_date' column in it, which states the difference in months between today and the ending_date.
    """
    df['current_date'] = date.today() + MonthBegin(1)
    df['current_date'] = pd.to_datetime(df['current_date'])
    df['EindeContract'] = pd.to_datetime(df['EindeContract']) + pd.Timedelta(days=1)
    df['end_date'] = df.apply(lambda row: (row['EindeContract'].year - row['current_date'].year) * 12 + row['EindeContract'].month - row['current_date'].month, axis =1).astype('int')
    return df
    
def data_preparation(buildings_df, distance = 5):
    """
    Prepares and returns data related to building information used by the optimization procedure.

    Parameters:
    distance (int): The distance in kilometers used to determine neighboring buildings. 
    Is passed on to the add_neighbors() function

    Return:
    DataFrame: A dataframe containing information for each building.
    Each row includes a unique id, monthly cost, contract ending date, 
    number of workers, neighboring buildings and building capacity
    Dictionary: A dictionary containing information for each building. 
    Each entry includes a unique id, monthly cost, contract ending date, 
    number of workers, neighboring buildings and building capacity
    """
    
    print("Preparing the data")
    
    # Make from the dataframe a list of dictionaries
    buildings = buildings_df.astype({'Pandcode': 'str',
                                     'Rent (Monthly)': 'int64',
                                     'Contractdue (Months)': 'int64',
                                     'Occupation (Max)': 'int64',
                                     'Neighbors': 'str',
                                     'Desks': 'int64'})
    buildings = buildings_df.to_dict('records')
    
    return buildings_df, buildings

def pand_optimizer(pand_dictionary):
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

    print("Optimizing...")
    # Create an LP problem instance
    prob = pulp.LpProblem("Building_Closure_Optimization", pulp.LpMinimize)
    
    # Decision variables
    x = pulp.LpVariable.dicts("x", [(i["Pandcode"], j) for i in pand_dictionary for j in range(1, 100)], cat='Binary')
    y = pulp.LpVariable.dicts("y", [(i["Pandcode"], j, k["Pandcode"]) for i in pand_dictionary for j in range(1, 100) for k in pand_dictionary if k["Pandcode"] in i["Neighbors"]], cat='Binary')
    z = pulp.LpVariable.dicts("z", [(i["Pandcode"], j, k["Pandcode"]) for i in pand_dictionary for j in range(1, 100) for k in pand_dictionary if k["Pandcode"] in i["Neighbors"]], cat='Binary')
    # Objective function
    moving_cost = 0
    prob += (
        pulp.lpSum(i["Rent (Monthly)"] * x[i["Pandcode"], j] for i in pand_dictionary for j in range(1, 100)) + 
        pulp.lpSum(moving_cost * k["Occupation (Max)"] * z[i["Pandcode"], j, k["Pandcode"]]
                   for i in pand_dictionary
                   for j in range(1, 100)
                   for k in pand_dictionary if k["Pandcode"] in i["Neighbors"])
    )
    # Constraints
    
    # Constraint 1
    for i in pand_dictionary:
        for j in range(1, i["Contractdue (Months)"] + 1):
            prob += x[i["Pandcode"], j] == 1
    
    # Constraint 2
    for i in pand_dictionary:
        for j in range(1, 100):
            prob += i["Occupation (Max)"] * x[i["Pandcode"], j] + pulp.lpSum(k["Occupation (Max)"] * y[k["Pandcode"], j, i["Pandcode"]] for k in pand_dictionary if k["Pandcode"] in i["Neighbors"]) <= i["Desks"]
    
    # Constraint 3
    for i in pand_dictionary:
        for j in range(1, 100):
            prob += pulp.lpSum(y[i["Pandcode"], j, k["Pandcode"]] for k in pand_dictionary if k["Pandcode"] in i["Neighbors"]) <= 1
    
    # Constraint 4
    for i in pand_dictionary:
        for j in range(1, 100):
            for k in pand_dictionary:
                if k["Pandcode"] in i["Neighbors"]:
                    prob += x[i["Pandcode"], j] >= y[k["Pandcode"], j, i["Pandcode"]]
    
    # Constraint 5
    for i in pand_dictionary:
        for j in range(1, 100):
            prob += x[i["Pandcode"], j] + pulp.lpSum(y[i["Pandcode"], j, k["Pandcode"]] for k in pand_dictionary if k["Pandcode"] in i["Neighbors"]) == 1
    
    # Constraint 6
    for i in pand_dictionary:
        for j in range(1, 99):  # Up to 36 because j+1 will be 37
            prob += x[i["Pandcode"], j] >= x[i["Pandcode"], j + 1]

    # Constraint 7: Ensuring that the moving variable is only 1 when y changes from 0 to 1.
    for i in pand_dictionary:
        for j in range(1,100):
            for k in pand_dictionary:
                if k["Pandcode"] in i["Neighbors"]:
                    if j == 1:
                        prob += z[i["Pandcode"], j, k["Pandcode"]] == y[i["Pandcode"], j, k["Pandcode"]]
                    else:
                        prob += z[i["Pandcode"], j, k["Pandcode"]] >= y[i["Pandcode"], j, k["Pandcode"]] - y[i["Pandcode"], j-1, k["Pandcode"]]
                        prob += z[i["Pandcode"], j, k["Pandcode"]] <= y[i["Pandcode"], j, k["Pandcode"]]
                        prob += z[i["Pandcode"], j, k["Pandcode"]] <= 1 - y[i["Pandcode"], j-1, k["Pandcode"]]

    # Solve the problem
    status = prob.solve()
                    
    if pulp.LpStatus[status] == 'Optimal':
        print("Found an optimal solution.")
    else:
        print("Could not find an optimal solution.")
        print("Continuing with the unoptimal output.")
    return x, y

def optimizer_to_dataframe(buildings_df, pand_dictionary, x, y, distance = 5):
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
    
    print("Preparing the optimized data")
    # Results

    df = pd.DataFrame(columns = ['Pandcode', 'Month', 'Status', 'pandcode_real'])
    # Extracting names and values for x and y   
    for i in pand_dictionary:
        Pandcode = i['id']
        for j in range(1, 100):
            Ysum = 0
            for k in pand_dictionary:
                if k["id"] in i["neighbors"] and y[i["id"], j, k["id"]].varValue == 1:
                    Reallocatie_pandcode = k['id']
                    Ysum += 1
            if Ysum == 0:
                Reallocatie_pandcode = Pandcode              
            month = j
            if x[i["id"], j].varValue == 1:
                status = 'Open'
            else:
                status = 'Closed'

            df.loc[len(df.index)] = [Pandcode, month, status, Reallocatie_pandcode]
            
    longlat_df = pd.read_csv('//10.178.145.69/div/Projecten/Pandbezetting/Brondata/Long_lat/DimLongLat.csv', sep=';').drop('PandcodeID', axis = 1)
    longlat_df['Latitude'] = pd.to_numeric(longlat_df['Latitude'].str.replace(',', '.'))
    longlat_df['Longitude'] = pd.to_numeric(longlat_df['Longitude'].str.replace(',', '.'))
    
    df = df.merge(buildings_df, left_on = 'Pandcode' , right_on = ['id'], how = 'left')
    df = df.merge(longlat_df, on = 'Pandcode', how = 'left')
    
    reallocatie_df = buildings_df
    reallocatie_df.columns = ['pandcode_real', 'kosten_real', 'end_date_real', 'workers_real', 'neighbors_real', 'capacity_real']
    
    df = df.merge(reallocatie_df, on = 'pandcode_real', how = 'left')

    today = pd.to_datetime("today")
    first_of_next_month = today + MonthBegin(1)
    df["DatumID"] = df["Month"].apply(lambda x: (first_of_next_month + pd.DateOffset(months=x)).replace(day=1).date())
    df = df.drop(['neighbors', 'neighbors_real'], axis = 1)
    df['Allowed_distance'] = distance
    return df

def execute_functions_distance(min_distance, max_distance):
    """
    Finds the optimal solution for a range of distances.

    Parameters:
    min_distance (int): The minimum distance the algorithm is used on.
    max_distance (int): The maximum distance the algorithm is used on.

    Return:
    df (DataFrame): A dataframe that contains the optimal solution of the algorithm for a range of distances.
    """
    df = pd.DataFrame()
    for distance in range(min_distance,max_distance):
        print(f"Calculating the optimal solution for distance: {distance}")
        buildings_df, buildings_dict = data_preparation(distance)
        x, y = pand_optimizer(buildings_dict)
        results_closing = optimizer_to_dataframe(buildings_df, buildings_dict, x, y, distance)
        df = pd.concat([df, results_closing], axis = 0, ignore_index = False)
    return df

def main():
    """
    Main function of the application

    This function serves as the entry point of the pand allocation algorithm program. 
    It calls other functions to perform tasks such as data preparation, model execution 
    and transforming the output into a readable format. It also handles top-level
    application logic.

    Returns:
        None
    """
    print("Main function started")
    pand_df = pd.read_csv('.\Dummy_data\example1.csv')
    print(pand_df)
    _, buildings_dict = data_preparation(pand_df)
    algorithm_df = pand_optimizer(buildings_dict)
    print("Main function succesfully finished.")

if __name__ == "__main__":
    main()


