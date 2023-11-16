import os

class PrimoUtils():
    def __init__(self):
        self.primo_api_key = os.environ.get("PRIMO_API_KEY")
        self.primo_api_host = os.environ.get("PRIMO_API_HOST")
        self.primo_api_limit = os.environ.get("PRIMO_API_LIMIT", 100)

    def generate_primo_api_request(self, llm_response):
        primo_api_request = self.primo_api_host + f"?scope=default_scope&tab=books&vid=HVD2&limit={self.primo_api_limit}&offset=0&apikey={self.primo_api_key}&q=any,contains,{'%20'.join(llm_response['keywords'])}&multiFacets=facet_rtype,include,books"
        if len(llm_response['libraries']) > 0:
            primo_api_request += "%7C,%7Cfacet_library,include," + '%7C,%7Cfacet_library,include,'.join(llm_response['libraries'])
        primo_api_request += "%7C,%7Cfacet_tlevel,include,available_onsite"
        return primo_api_request

    def shrink_results_for_llm(self, results, libraries):
        reduced_results = {}
        for result in results:
            for holding in result['delivery']['holding']:
                new_object = {
                    # TODO: We previously were using ['pnx']['addata']['btitle'] but that is not always present. We will need to come up with a prioritization order to determine which title to use.
                    'title': result['pnx']['sort']['title'],
                    # TODO: Corinna wants us to use ['pnx']['addata']['aulast'] but that author is not always present and we will need to come up with a prioritization order to determine which author to use.
                    'author': result['pnx']['sort']['author'],
                    'callNumber': holding['callNumber']
                }
                if holding['libraryCode'] in libraries:
                    if not holding['libraryCode'] in reduced_results:
                        reduced_results[holding['libraryCode']] = []
                    reduced_results[holding['libraryCode']].append(new_object)
        return reduced_results
