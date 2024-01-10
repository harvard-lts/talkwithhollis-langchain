import pytest
from datetime import datetime

from freezegun import freeze_time
# freeze time is using UTC, while the application is receiving library hours in UTC, so there will be descrepancies between
# the hours string sent to is_open_now and the time that is being frozen

from app.utils.libcalutils import LibCalUtils

@pytest.mark.asyncio
@freeze_time("2012-01-14")
async def test_is_open_now_unknown_time_string():
	libcal_utils = LibCalUtils()
	result = await libcal_utils.is_open_now("nonsense_words")
	print(result)
	assert result == False
	assert datetime.now() == datetime(2012, 1, 14)

@pytest.mark.asyncio
@freeze_time("2024-01-01 20:00:01") # 8:00pm UTC -> 3:00pm EST
async def test_is_open_now_open_library():
	libcal_utils = LibCalUtils()
	result = await libcal_utils.is_open_now("Open from 10:00am to 4:00pm")
	assert result == True

@pytest.mark.asyncio
@freeze_time("2024-01-01 10:00:01") # 10:00am UTC -> 5:00am EST
async def test_is_open_now_closed_library_before_hours():
	libcal_utils = LibCalUtils()
	result = await libcal_utils.is_open_now("Open from 10:00am to 4:00pm")
	assert result == False

@pytest.mark.asyncio
@freeze_time("2024-01-01 23:00:01") # 23:00am UTC -> 5:00pm EST
async def test_is_open_now_closed_library_after_hours():
	libcal_utils = LibCalUtils()
	result = await libcal_utils.is_open_now("Open from 10:00am to 4:00pm")
	assert result == False

@pytest.mark.asyncio
@freeze_time("2024-01-01 20:00:01") # 8:00pm UTC -> 3:00pm EST
async def test_is_open_now_closed_library_after_hours():
	libcal_utils = LibCalUtils()
	result = await libcal_utils.is_open_now("Closed")
	assert result == False

@pytest.mark.asyncio
@freeze_time("2024-01-01 20:00:01") # 8:00pm UTC -> 3:00pm EST
async def test_is_open_now_closed_library_after_hours():
	libcal_utils = LibCalUtils()
	result = await libcal_utils.is_open_now("Open 24 Hours")
	assert result == True
