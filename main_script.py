import logging
import functions.pulp_optimizer as po
import pandas as pd

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
    config = po.load_config()
    
    if config is None:
        logging.error("Configuration loading failed. Exiting.")
        return
    
    # Set up logging
    logging.basicConfig()
    logging.getLogger().setLevel(config.get('logging_level'))

    logging.info("Main function started")

    data_file = config.get('data_file')

    try:
        pand_df = pd.read_csv(data_file)
    except Exception as e:
        logging.error(f"Failed to load data file: {e}")
        return
    
    buildings_df, buildings_dict = po.data_preparation(pand_df)
    if buildings_df is None:
        logging.error("Data preparation failed. Exiting.")
        return
    
    timehorizon = config.get("timehorizon")
    x, y  = po.pand_optimizer(buildings_dict, timehorizon + 1)
    results_closing = po.optimizer_to_dataframe(buildings_df, buildings_dict, x, y, timehorizon + 1)
    
    po.save_results(results_closing)

    logging.info("Main function succesfully finished.")

if __name__ == "__main__":
    main()