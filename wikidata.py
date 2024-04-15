import datetime
from unittest import TestCase

from SPARQLWrapper import SPARQLWrapper, JSON
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta


class Guru:
    def __init__(self, endpoint: str = 'https://query.wikidata.org/sparql'):
        self.endpoint = endpoint
        self.sparql = SPARQLWrapper(self.endpoint)

    @staticmethod
    def person_query(person: str):
        """
        Creates query to select DOB and DOD for a given name of a politician.
        :param person: name of politician e.g. Tony Blair
        :return: query
        """
        query = f"""SELECT DISTINCT ?person ?personLabel ?date_of_birth ?date_of_death WHERE {{
                    ?person wdt:P31 wd:Q5;
                    wdt:P106 wd:Q82955;
                    wdt:P569 ?date_of_birth;
                    ?label "{person}"@en.
                    OPTIONAL {{
                    ?person wdt:P570 ?date_of_death.    
                    }}
                    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
                    }}"""
        return query

    @staticmethod
    def city_query(city: str):
        """
        Creates query to select population of given capital city.
        :param city: name of capital city e.g: London
        :return: query
        """
        query = f"""SELECT DISTINCT ?city ?cityLabel ?population WHERE {{ 
                    ?city wdt:P31 wd:Q5119; 
                    ?label "{city}"@en. 
                    OPTIONAL {{ ?city wdt:P1082 ?population. }} 
                    SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
                    }}"""
        return query

    def run_query(self, query):
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query().convert()
        return results

    def get_age(self, person):
        """
        get_age function runs query to get DOB and DOD of politician and then calculates his/her age.
        Function raises exceptions:
         IndexError when person is not found
         ValueError when query returns more than one record
         ValueError when person is already dead
        :param person:  name of politician e.g. Tony Blair
        :return: age as string
        """
        query = self.person_query(person)
        results = self.run_query(query)
        bindings_length = len(results['results']['bindings'])
        if bindings_length == 0:
            raise IndexError(person + " has not been found")
        elif bindings_length > 1:
            raise ValueError("Ambiguous result. " + str(bindings_length) + " records returned")
        elif 'date_of_death' in results['results']['bindings'][0].keys():
            raise ValueError(person + " is dead")
        else:
            dob_result = results['results']['bindings'][0]['date_of_birth']['value']
            today = datetime.date.today()
            dob = parse(dob_result).date()
            age = str(relativedelta(today, dob).years)
        return age

    def get_population(self, city):
        """
        get_population function runs query to get population of capital city.
        Function raises exceptions:
         IndexError when capital city is not found
         ValueError when query returns more than one record
        :param city: name of capital city e.g. London
        :return: population
        """
        query = self.city_query(city)
        results = self.run_query(query)
        bindings_length = len(results['results']['bindings'])
        if bindings_length == 0:
            raise IndexError(city + " has not been found")
        elif bindings_length > 1:
            raise ValueError("Ambiguous result. " + str(bindings_length) + " records returned")
        else:
            population = results['results']['bindings'][0]['population']['value']

        return population

    def ask(self, question: str):
        """
        ask function supports two questions:
        'how old is <name_of_politician>' and 'what is the population of <name_of_capital_city>'
        Function raises exceptions:
         ValueError if there is missing persons' name in age question
         ValueError if there is missing city name in population question
         ValueError for invalid question
         IndexError when person is not found
         ValueError when query returns more than one record
         ValueError when person is already dead
         IndexError when capital city is not found
         ValueError when query returns more than one record
        :param question: e.g. 'how old is Tony Blair' or 'what is the population of London'
        :return: age for 'how old' question or population for 'what is the population' question
        """
        age_question = "how old is "
        population_question = "what is the population of "
        question_lowercase = question.lower()
        if age_question in question_lowercase:
            person = question_lowercase.replace(age_question, '')
            if not person or not person.strip():
                raise ValueError("Missing person's name")
            else:
                result = self.get_age(person.strip().title())
        elif population_question in question_lowercase:
            city = question_lowercase.replace(population_question, '')
            if not city or not city.strip():
                raise ValueError("Missing city name")
            else:
                result = self.get_population(city.strip().title())
        else:
            raise ValueError("Invalid question: " + question)

        return result


class TestGuru(TestCase):

    def test_ask(self):
        guru: Guru = Guru()
        # note these values may change a little as time moves on
        self.assertEqual('70', guru.ask('how old is Tony Blair'))
        self.assertEqual('77', guru.ask('how old is trump'))
        with self.assertRaisesRegex(ValueError, "Ambiguous result. 2 records returned"):
            guru.ask('how old is Lincoln')
        with self.assertRaisesRegex(ValueError, "Abraham Lincoln is dead"):
            guru.ask('how old is Abraham Lincoln')
        self.assertEqual('62', guru.ask('how old is   Barack Obama'))
        with self.assertRaisesRegex(ValueError, "Missing person's name"):
            guru.ask('how old is ')
        self.assertEqual('8799728', guru.ask('what is the population of London'))
        self.assertEqual('8799728', guru.ask('what is the population of lOndon'))
        self.assertEqual('2145906', guru.ask('What is the population of Paris'))
        with self.assertRaisesRegex(ValueError, "Missing city name"):
            guru.ask('what is the population of ')
        with self.assertRaisesRegex(IndexError, "Narnia has not been found"):
            guru.ask('what is the population of Narnia')
        with self.assertRaisesRegex(ValueError, "Invalid question: what is area of Berlin"):
            guru.ask('what is area of Berlin')
