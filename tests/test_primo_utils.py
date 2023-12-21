from app.utils.primo import PrimoUtils
import app.config as config
from app.config import Settings

config.settings = Settings(_env_file = 'test.env')

def test_generate_primo_api_request():
	print(config.settings)
	primo_utils = PrimoUtils()
	result = primo_utils.generate_primo_api_request({'keywords': ['abc123'], 'libraries': ['FUN']})
	assert result == 'https://fakehost.exlibrisgroup.com/primo/v1/search?q=any,contains,abc123&apikey=primo_api_key&scope=default_scope&tab=books&vid=HVD2&limit=100&offset=0&multiFacets=facet_rtype,include,books%7C,%7Cfacet_library,include,FUN%7C,%7Cfacet_tlevel,include,available_onsite'

def test_generate_primo_api_request_multiple_keywords_and_libraries():
	primo_utils = PrimoUtils()
	result = primo_utils.generate_primo_api_request({'keywords': ['abc123', 'def456', 'ghi789'], 'libraries': ['FUN', 'WID', 'LAM']})
	assert result == 'https://fakehost.exlibrisgroup.com/primo/v1/search?q=any,contains,abc123%20def456%20ghi789&apikey=primo_api_key&scope=default_scope&tab=books&vid=HVD2&limit=100&offset=0&multiFacets=facet_rtype,include,books%7C,%7Cfacet_library,include,FUN%7C,%7Cfacet_library,include,WID%7C,%7Cfacet_library,include,LAM%7C,%7Cfacet_tlevel,include,available_onsite'

def test_generate_hollis_api_request():
	primo_utils = PrimoUtils()
	result = primo_utils.generate_hollis_api_request({'keywords': ['abc123', 'def456', 'ghi789'], 'libraries': ['FUN', 'WID', 'LAM']})
	assert result == 'https://fakehost.harvard.edu/primo-explore/search?query=any,contains,abc123%20def456%20ghi789&search_scope=default_scope&tab=books&vid=HVD2&limit=100&offset=0&mfacet=library,include,FUN,1,lk&mfacet=library,include,WID,1,lk&mfacet=library,include,LAM,1,lk&facet=tlevel,include,available_onsite,lk&facet=rtype,include,books,lk'

def test_generate_hollis_api_request_multiple_keywords_and_libraries():
	primo_utils = PrimoUtils()
	result = primo_utils.generate_hollis_api_request({'keywords': ['abc123', 'def456', 'ghi789'], 'libraries': ['FUN', 'WID', 'LAM']})
	assert result == 'https://fakehost.harvard.edu/primo-explore/search?query=any,contains,abc123%20def456%20ghi789&search_scope=default_scope&tab=books&vid=HVD2&limit=100&offset=0&mfacet=library,include,FUN,1,lk&mfacet=library,include,WID,1,lk&mfacet=library,include,LAM,1,lk&facet=tlevel,include,available_onsite,lk&facet=rtype,include,books,lk'
