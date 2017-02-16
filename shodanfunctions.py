from base import dict_add_source_prefix
from base import dict_clean_empty
import configparser
import shodan
import json
import sys
import os


def get_new_shodan_api_object():
    """Returns initialised Shodan API object"""
    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.realpath(__file__)) + "/config.ini")
    key = (config['SectionOne']['SHODAN_API_KEY'])
    return shodan.Shodan(key)


def to_es_convert(input_dict):
    """Returns dict ready to be used by the Elastic Stack."""
    try:
        # set ip and ip_int
        ip_int = input_dict['ip']
        del input_dict['ip']
        input_dict['ip'] = input_dict['ip_str']
        del input_dict['ip_str']
        input_dict['ip_int'] = ip_int
    except KeyError:
        try:
            input_dict['ip'] = input_dict['ip_str']
            del input_dict['ip_str']
        except KeyError:
            print(input_dict)
            print('Missing required \'ip\' field in the element above. Exiting now...')
            sys.exit(1)

    # if present, convert ssl.cert.serial to string
    try:
        input_dict['ssl']['cert']['serial'] = str(input_dict['ssl']['cert']['serial'])
    except KeyError:
        pass
    # if present, convert ssl.dhparams.generator to string
    try:
        input_dict['ssl']['dhparams']['generator'] = str(input_dict['ssl']['dhparams']['generator'])
    except (KeyError, TypeError):
        pass

    try:
        # rename_shodan.modules to protocols (used as prefix per banner for combining multiple banners into 1 IP)
        input_dict['protocols'] = input_dict['_shodan']['module']
        # the rest of the data in _shodan is irrelevant
        del input_dict['_shodan']
    except KeyError:
        pass
    # asn to int
    try:
        input_dict['asn'] = int((input_dict['asn'])[2:])
    except KeyError:
        pass
    try:
        # rename location.country_name to location.country
        input_dict['location']['country'] = input_dict['location']['country_name']
        del input_dict['location']['country_name']
        # rename latitude and longitude for geoip
        input_dict['location']['geo'] = {}
        input_dict['location']['geo']['lat'] = input_dict['location']['latitude']
        input_dict['location']['geo']['lon'] = input_dict['location']['longitude']
        del input_dict['location']['latitude']
        del input_dict['location']['longitude']
    except KeyError:
        pass

    # Limit the number of fields
    input_dict = limit_nr_of_elements(input_dict)

    # prefix non-nested fields with 'shodan'
    input_dict = dict_add_source_prefix(input_dict, 'shodan', str(input_dict['protocols']))
    return input_dict


def limit_nr_of_elements(input_dict):
    """Converts some of the JSON elements containing (too) many nested elements to 1 string element.
    This prevents Elasticsearch from making too many fields, so it is still manageable in Kibana.
    """
    try:
        input_dict['http']['components'] = str(
            input_dict['http']['components'])
    except KeyError:
        pass
    try:
        input_dict['elastic'] = str(
            input_dict['elastic'])
    except KeyError:
        pass
    return input_dict


def to_file_shodan(queries, path_output_file, should_convert):
    """Makes a Shodan API call with each given query and writes results to output file
    :param queries: Collection of strings which present Shodan queries
    :param path_output_file: String which points to existing output file
    :param should_convert: Boolean if results should be converted
    """
    api = get_new_shodan_api_object()
    nr_total_results = 0
    failed_queries = set()
    for query in queries:
        print('\"' + query + '\"')
        results = []
        try:
            for banner in api.search_cursor(query):
                banner = dict_clean_empty(banner)
                if should_convert:
                    to_es_convert(banner)
                results.append(json.dumps(banner) + '\n')
                print('\r' + str(len(results)) + ' results fetched...', end='')
        except shodan.APIError as e:
            print('Error: ', e)
            failed_queries.add(failed_queries)
        with open(path_output_file, "a") as output_file:
            for banner in results:
                output_file.write(banner)
        print('\r' + str(len(results)) + ' results written.')
        nr_total_results += len(results)
    # Print failed queries if present
    if not failed_queries == set():
        print('Failed queries: ', failed_queries)
    if should_convert:
        print(str(nr_total_results) + ' total results converted and written in ' + path_output_file)
    else:
        print(str(nr_total_results) + ' total results written in ' + path_output_file)


def get_input_choice():
    """Returns input_choice represented as integer"""
    items = ['1', '2', '3', '4']
    input_choice = '0'
    while input_choice not in items:
        input_choice = input("Console input[1], CIDR file input[2], csv file input[3] or query file input[4]?")
    return int(input_choice)


def get_user_input_console_queries():
    """Returns a non empty set of query strings"""
    queries = set()
    done = False
    print('Enter Shodan queries, one at a time. Enter \'4\' when done.')
    while not done:
            query = ''
            while query is '':
                query = input("Query:")
            if query is '4':
                if queries != set():
                    done = True
            else:
                queries.add(query)
    return queries
