import argparse
import sys


def main():
    command_str = ' '.join(sys.argv)
    print(f'Executing command:{command_str}')
    parser = argparse.ArgumentParser(description='Helical-pdqueiros ArgParser')
    parser.add_argument('execution_type', help='[required]\tExecution mode', type=str, choices=['split_data', 'process_data', 'fine_tune'])
    # you coul add more arguments, but this is ok for now
    args = parser.parse_args()
    execution_type = args.execution_type
    # since we don't have separate containers, I'm importing by requirement to avoid loading everything for the fine-tuning unless necessary
    if execution_type == 'split_data':
        from helical_pdqueiros.jobs.cell_type_annotation.split_data import SplitDataJob
        job = SplitDataJob()
    elif execution_type == 'process_data':
        from helical_pdqueiros.jobs.cell_type_annotation.process_data import ProcessDataJob
        job = ProcessDataJob()
    elif execution_type == 'fine_tune':
        from helical_pdqueiros.jobs.cell_type_annotation.fine_tune import FineTuneJob
        job = FineTuneJob()
    else:
        raise Exception(f'Invalid execution type: {execution_type}')
    job.run()

if __name__ == '__main__':
    main()
