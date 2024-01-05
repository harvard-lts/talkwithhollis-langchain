import json, os
import pytest
import asyncio

from app.utils.primo import PrimoUtils

llm_result_one_keyword_one_library = {'keywords': ['abc123'], 'libraries': ['FUN']}
llm_result_multiple_keywords_and_libraries = {'keywords': ['abc123', 'def456', 'ghi789'], 'libraries': ['FUN', 'WID', 'LAM']}

with open(os.path.abspath('./tests/test_data/filtered_primo_results.json')) as f:
    filtered_primo_results = json.load(f)

with open(os.path.abspath('./tests/test_data/unfiltered_primo_results.json')) as f:
	unfiltered_primo_results = json.load(f)

with open(os.path.abspath('./app/schemas/libraries_acceptable_sublocations.json')) as f:
	libraries_acceptable_sublocations = json.load(f)

def test_generate_primo_api_request():
	primo_utils = PrimoUtils()
	result = primo_utils.generate_primo_api_request(llm_result_one_keyword_one_library)
	assert result == 'https://fakehost.exlibrisgroup.com/primo/v1/search?q=any,contains,abc123&apikey=primo_api_key&scope=default_scope&tab=books&vid=HVD2&limit=100&offset=0&multiFacets=facet_rtype,include,books%7C,%7Cfacet_library,include,FUN%7C,%7Cfacet_tlevel,include,available_onsite'

def test_generate_primo_api_request_multiple_keywords_and_libraries():
	primo_utils = PrimoUtils()
	result = primo_utils.generate_primo_api_request(llm_result_multiple_keywords_and_libraries)
	assert result == 'https://fakehost.exlibrisgroup.com/primo/v1/search?q=any,contains,abc123%20def456%20ghi789&apikey=primo_api_key&scope=default_scope&tab=books&vid=HVD2&limit=100&offset=0&multiFacets=facet_rtype,include,books%7C,%7Cfacet_library,include,FUN%7C,%7Cfacet_library,include,WID%7C,%7Cfacet_library,include,LAM%7C,%7Cfacet_tlevel,include,available_onsite'

def test_generate_hollis_api_request():
	primo_utils = PrimoUtils()
	result = primo_utils.generate_hollis_api_request(llm_result_one_keyword_one_library)
	assert result == 'https://fakehost.harvard.edu/primo-explore/search?query=any,contains,abc123&search_scope=default_scope&tab=books&vid=HVD2&limit=100&offset=0&mfacet=library,include,FUN,1,lk&facet=tlevel,include,available_onsite,lk&facet=rtype,include,books,lk'

def test_generate_hollis_api_request_multiple_keywords_and_libraries():
	primo_utils = PrimoUtils()
	result = primo_utils.generate_hollis_api_request(llm_result_multiple_keywords_and_libraries)
	assert result == 'https://fakehost.harvard.edu/primo-explore/search?query=any,contains,abc123%20def456%20ghi789&search_scope=default_scope&tab=books&vid=HVD2&limit=100&offset=0&mfacet=library,include,FUN,1,lk&mfacet=library,include,WID,1,lk&mfacet=library,include,LAM,1,lk&facet=tlevel,include,available_onsite,lk&facet=rtype,include,books,lk'

def test_generate_primo_query():
	primo_utils = PrimoUtils()
	result = primo_utils.generate_primo_query(llm_result_one_keyword_one_library)
	assert result == 'q=any,contains,abc123'
	
def test_generate_primo_query_multiple_keywords_and_libraries():
	primo_utils = PrimoUtils()
	result = primo_utils.generate_primo_query(llm_result_multiple_keywords_and_libraries)
	assert result == 'q=any,contains,abc123%20def456%20ghi789'

@pytest.mark.asyncio
async def test_get_available_results_up_to_limit():
	primo_utils = PrimoUtils()
	result = await primo_utils.get_available_results_up_to_limit(unfiltered_primo_results, ["LAM", "GUT", "WID"], 10)
	assert len(result) == 10

	# Ensure that only records only contain matching holdings, the rest should be filtered out
	for record in result:
		for holding in record['delivery']['holding']:
			assert holding['libraryCode'] in ["LAM", "GUT", "WID"]

			# also ensure that these holdings are only in acceptable sublocations
			sublocations_for_library = libraries_acceptable_sublocations[holding['libraryCode']].keys()
			assert holding['subLocationCode'] in sublocations_for_library

def test_shrink_results_for_llm():
	primo_utils = PrimoUtils()
	result = primo_utils.shrink_results_for_llm(filtered_primo_results, ["AJP", "TOZ", "LAM", "WID"])

	ajp_results = result['AJP']
	ajp_results[0]['title'] == "<a href='http://id.lib.harvard.edu/alma/990142840400203941/catalog' target='_blank'>Birds</a>"
	ajp_results[0]['callNumber'] == "(Ac T34 )"
	ajp_results[0]['author'] == ["Theodorou"]
	ajp_results[1]['title'] == "<a href='http://id.lib.harvard.edu/alma/990128046100203941/catalog' target='_blank'>Birds</a>"
	ajp_results[1]['callNumber'] == "(Ac Al2 )"
	ajp_results[1]['author'] == ["Peterson", "Alden", "Sill"]

	toz_results = result['TOZ']
	toz_results[0]['title'] == "<a href='http://id.lib.harvard.edu/alma/990125639740203941/catalog' target='_blank'>Birds</a>"
	toz_results[0]['callNumber'] == "(CC79.5.B57 S47 2009 )"
	toz_results[0]['author'] == ["Serjeantson"]

	lam_results = result['LAM']
	lam_results[0]['title'] == "<a href='http://id.lib.harvard.edu/alma/990000948030203941/catalog' target='_blank'>Birds</a>"
	lam_results[0]['callNumber'] == "(PA3875.A8 B5 x, 1987 )"
	lam_results[0]['author'] == ["Sommerstein"]
	lam_results[1]['title'] == "<a href='http://id.lib.harvard.edu/alma/990078361120203941/catalog' target='_blank'>The Birds</a>"
	lam_results[1]['callNumber'] == "(PN1997.B475 P35 1998 )"
	lam_results[1]['author'] == ["Paglia"]

	wid_results = result['WID']
	wid_results[0]['title'] == "<a href='http://id.lib.harvard.edu/alma/990078361120203941/catalog' target='_blank'>The Birds</a>"
	wid_results[0]['callNumber'] == "(PN1997.B4753 P34 1998x )"
	wid_results[0]['author'] == ["Paglia"]
