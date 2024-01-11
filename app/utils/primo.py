import copy
import os
import re

from .file import FileUtils
from app.config import settings

class PrimoUtils():
    def __init__(self):
        self.primo_api_key = settings.primo_api_key
        self.primo_api_host = settings.primo_api_host
        self.primo_api_limit = settings.primo_api_limit
        self.hollis_api_host = settings.hollis_api_host

    def generate_primo_api_request(self, llm_response):
        primo_api_query = self.generate_primo_query(llm_response)
        primo_api_request = f"{self.primo_api_host}?{primo_api_query}&apikey={self.primo_api_key}"
        primo_api_request += f"&scope=default_scope&tab=books&vid=HVD2&limit={self.primo_api_limit}&offset=0"
        primo_api_request += f"&multiFacets=facet_rtype,include,books"
        if len(llm_response['libraries']) > 0:
            primo_api_request += "%7C,%7Cfacet_library,include," + '%7C,%7Cfacet_library,include,'.join(llm_response['libraries'])
        primo_api_request += "%7C,%7Cfacet_tlevel,include,available_onsite"
        return primo_api_request

    def generate_hollis_api_request(self, llm_response):
        primo_api_query = self.generate_primo_query(llm_response, True)
        hollis_api_request = f"{self.hollis_api_host}?{primo_api_query}"
        hollis_api_request += f"&search_scope=default_scope&tab=books&vid=HVD2&limit={self.primo_api_limit}&offset=0"
        library_query = ""
        if len(llm_response['libraries']) > 0:
          for library in llm_response['libraries']:
            library_query += f"mfacet=library,include,{library},1,lk&"
          # remove trailing &
          library_query = library_query[:-1]
        hollis_api_request += f"&{library_query}"
        hollis_api_request += "&facet=tlevel,include,available_onsite,lk&facet=rtype,include,books,lk"
        return hollis_api_request

    def generate_primo_query(self, llm_response, hollis=False):
        qparam = "q"
        if hollis:
            qparam = "query"
        query_string = f"{qparam}=any,contains,{'%20'.join(llm_response['keywords'])}"
        return query_string

    def shrink_results_for_llm(self, results, libraries):
        reduced_results = {}
        for result in results:
            # This is to prevent duplicate results from the same library from being added to the list, libraries can have more than one holding of a book, and displaying
            # several records of identical books at the same library is confusing for the user
            already_added_libraries = []

            for holding in result['delivery']['holding']:
                # btitle is preferred, but jtitle should always exist
                try:
                    title = result['pnx']['addata']['btitle']
                except:
                    title = result['pnx']['addata']['jtitle']

                permalink = result.get('pnx', {}).get('display', {}).get('lds03', {})
                if permalink and len(permalink) > 0:
                    hollis_link = re.search(r'href=\"(.*?)\"', permalink[0]).group(1)
                    title = "<a href='{}' target='_blank'>{}</a>".format(hollis_link, ', '.join(title))

                try:
                    author = result['pnx']['addata']['aulast']
                except:
                    author = None

                new_object = {
                    'title': title,
                    'callNumber': holding['callNumber']
                }

                if author:
                    new_object['author'] = author

                # Add to the list only if that book has not been added for that library AND that library is in the list of libraries we want to include
                if holding['libraryCode'] not in already_added_libraries and holding['libraryCode'] in libraries:
                    already_added_libraries.append(holding['libraryCode'])

                    if not holding['libraryCode'] in reduced_results:
                        reduced_results[holding['libraryCode']] = []
                    reduced_results[holding['libraryCode']].append(new_object)
        return reduced_results
    
    async def get_available_results_up_to_limit(self, primo_results, libraries, result_limit):
        # This method is to create a list, up to the configured result limit, of books that correspond to availability at the requested libraries
        acceptable_library_sublocations = await FileUtils().get_libraries_sublocations_json()

        filtered_results = []
        for result in primo_results:
            # Check results until we find an amount that meet the criteria equal equal to the limit
            relevant_holdings = []
            for holding in result.get('delivery', {}).get('holding', []):
                # check if the holding is at a requested library and available
                libraryCode = holding.get('libraryCode')
                if libraryCode in libraries and holding['availabilityStatus'] == 'available':
                    # if so, we check against that library's allowed sublocation codes (only books in certain sublocations can be checked out)
                    if holding['subLocationCode'] in acceptable_library_sublocations[libraryCode].keys():
                        relevant_holdings.append(holding)

            if len(relevant_holdings) > 0:
                transformed_result = copy.deepcopy(result)
                transformed_result['delivery']['holding'] = relevant_holdings
                filtered_results.append(transformed_result)

            if len(filtered_results) >= result_limit:
                break

        return filtered_results

