import os
from app.config import settings

class PrimoUtils():
    def __init__(self):
        self.primo_api_key = settings.primo_api_key
        self.primo_api_host = settings.primo_api_host
        self.primo_api_limit = settings.primo_api_limit
        self.hollis_api_host = settings.hollis_api_host
        self.default_params = f"scope=default_scope&tab=books&vid=HVD2&limit={self.primo_api_limit}&offset=0"

    def generate_primo_api_request(self, llm_response):
        primo_api_query = self.generate_primo_query(llm_response)
        primo_api_request = f"{self.primo_api_host}?{self.default_params}&apikey={self.primo_api_key}&{primo_api_query}&multiFacets=facet_rtype,include,books"
        if len(llm_response['libraries']) > 0:
            primo_api_request += "%7C,%7Cfacet_library,include," + '%7C,%7Cfacet_library,include,'.join(llm_response['libraries'])
        primo_api_request += "%7C,%7Cfacet_tlevel,include,available_onsite"
        return primo_api_request

    def generate_hollis_api_request(self, llm_response):
        primo_api_query = self.generate_primo_query(llm_response)
        hollis_api_request = f"{self.hollis_api_host}?{self.default_params}&{primo_api_query}"
        if len(llm_response['libraries']) > 0:
            # TOCO: Convert query params to mfacet
            # mfacet=library,include,WID,1,lk&
            hollis_api_request += "%7C,%7Cfacet_library,include," + '%7C,%7Cfacet_library,include,'.join(llm_response['libraries'])
        hollis_api_request = "facet=tlevel,include,available_onsite,lk&facet=rtype,include,books,lk"
        return primo_api_request

    def generate_primo_query(self, llm_response):
        return f"q=any,contains,{'%20'.join(llm_response['keywords'])}"

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

                try:
                    author = result['pnx']['addata']['aulast']
                except:
                    author = None

                new_object = {
                    # TODO: We previously were using ['pnx']['addata']['btitle'] but that is not always present. We will need to come up with a prioritization order to determine which title to use.
                    'title': title,
                    # TODO: Corinna wants us to use ['pnx']['addata']['aulast'] but that author is not always present and we will need to come up with a prioritization order to determine which author to use.
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
