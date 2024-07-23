from optimise_building_selection import execute_functions_distance


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
    try:
        algorithm_df = execute_functions_distance(0, 20)
        print("Main function succesfully finished.")
    except:
        print("An issue has occurred while running the main function.")

if __name__ == "__main__":
    main()