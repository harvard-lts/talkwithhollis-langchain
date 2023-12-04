import os
from app.config import settings

class PrimoUtils():
    def __init__(self):
        self.primo_api_key = settings.primo_api_key
        self.primo_api_host = settings.primo_api_host
        self.primo_api_limit = settings.primo_api_limit

    def generate_primo_api_request(self, llm_response):
        primo_api_request = self.primo_api_host + f"?scope=default_scope&tab=books&vid=HVD2&limit={self.primo_api_limit}&offset=0&apikey={self.primo_api_key}&q=any,contains,{'%20'.join(llm_response['keywords'])}&multiFacets=facet_rtype,include,books"
        if len(llm_response['libraries']) > 0:
            primo_api_request += "%7C,%7Cfacet_library,include," + '%7C,%7Cfacet_library,include,'.join(llm_response['libraries'])
        primo_api_request += "%7C,%7Cfacet_tlevel,include,available_onsite"
        return primo_api_request

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
