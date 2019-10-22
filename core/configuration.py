import os
import json
import pandas as pd
import configparser
import logging


class ConfigurationManager(object):
    """
    Configuration Manager

    Class that manages the configuration of all other modules.

    """

    def __init__(self):
        """
        Initializes Configuration Manager, config not set up yet
        """
        logging.basicConfig(level=logging.DEBUG,
            format='[ConfigurationManager] %(asctime)s %(levelname)s %(message)s')
        self.question_format = "{question} [default = {default}] "
        self._config = None

    def reset(self):
        """
        Resets the configuration by deleting it. Bootstrap must be called so that
        the class works as intended.
        """
        self._config = None
        return self

    def bootstrap(self, config_filepath="core/configuration.ini", 
                    question_filepath="core/questions.csv", input_function=None):
        """
        Do nothing if config instance already exists. Otherwise, check if
        core/configuration.ini exists. If not, call _run_setup_mode. Then load
        the config instance from configuration.ini
        """
        if self._config:
            return False
        self.input_function = input_function if input_function else input
        self.config_filepath = config_filepath
        self.question_filepath = question_filepath
        if not os.path.isfile(self.config_filepath):
            self._run_setup_mode(
                self.config_filepath, 
                self.question_filepath, 
                self.input_function
            )
        else:
            self._config = configparser.ConfigParser()
            self._config.read(self.config_filepath)
        return True


    def _run_setup_mode(self, config_filepath, question_filepath, user_input):
        """
        Create configuration.ini with the user_input function. In testing,
        this is a deterministic lambda function.
        Otherwise, the user_input function actually draws upon user input.
        """

        # Go through each question in questions.csv. If question is SECRET,
        # keep track of corresponding section. Otherwise, ask user question.
        secret_section_message = "; DO NOT MODIFY THIS SECTION\n"
        config = configparser.ConfigParser()
        rows = [r[1] for r in pd.read_csv(question_filepath).iterrows()]
        secret_sections = set([])
        for row in rows:
            question = row['question']
            section = row['section']
            key = row['key']
            default = row['default'] 
            if question == 'SECRET':
                answer = default
                secret_sections.add(section)
            else:
                complete_question = self.question_format.format(
                    question=question, 
                    default=default
                )
                answer = user_input(complete_question)
                answer = answer if answer else default
            if section not in config:
                config[section] = {} 
            config[section][key] = answer
        with open(self.config_filepath, 'w') as configfile:
            config.write(configfile)
        
        # For all secret sections, add secret_section_message as a comment.
        with open(config_filepath, "r") as f:
            lines = f.readlines()
        for secret_section in secret_sections:
            index = lines.index("[{}]\n".format(secret_section))
            lines.insert(index, secret_section_message)
        with open(config_filepath, "w") as f:
            f.write("".join(lines))
        self._config = config


    def get_config(self):
        """
        Returns the configuration.
        """
        if not self._config:
            raise Exception("Configuration Manager needs to be bootstrapped first.")
        return self._config