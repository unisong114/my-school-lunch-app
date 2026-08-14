"""급식 분석 페이지에서 사용하는 무작위 학교 표본 목록.

NEIS `schoolInfo` 조회 결과로 확인한 실제 학교 정보 중 지역·학교급이
다양하도록 미리 선정한 10개 학교입니다. 급식 분석 페이지는 이 표본에서
사용자가 비교할 2개 학교를 선택합니다.
"""

from __future__ import annotations

from .models import School

SAMPLE_SCHOOLS: list[School] = [
    School(
        eduOfficeCode="B10",
        eduOfficeName="서울특별시교육청",
        schoolCode="7010083",
        schoolName="서울고등학교",
        schoolKind="고등학교",
        region="서울특별시",
        address="서울특별시 서초구 효령로 197",
    ),
    School(
        eduOfficeCode="B10",
        eduOfficeName="서울특별시교육청",
        schoolCode="7010059",
        schoolName="경기고등학교",
        schoolKind="고등학교",
        region="서울특별시",
        address="서울특별시 강남구 영동대로 643",
    ),
    School(
        eduOfficeCode="C10",
        eduOfficeName="부산광역시교육청",
        schoolCode="7181088",
        schoolName="부산중학교",
        schoolKind="중학교",
        region="부산광역시",
        address="부산광역시 동구 초량로40번길 29",
    ),
    School(
        eduOfficeCode="D10",
        eduOfficeName="대구광역시교육청",
        schoolCode="7271009",
        schoolName="대구중학교",
        schoolKind="중학교",
        region="대구광역시",
        address="대구광역시 남구 대봉로 120",
    ),
    School(
        eduOfficeCode="E10",
        eduOfficeName="인천광역시교육청",
        schoolCode="7310057",
        schoolName="인천고등학교",
        schoolKind="고등학교",
        region="인천광역시",
        address="인천광역시 미추홀구 경원대로 804",
    ),
    School(
        eduOfficeCode="F10",
        eduOfficeName="전남광주통합특별시교육청(광주)",
        schoolCode="7140319",
        schoolName="광주고등학교",
        schoolKind="고등학교",
        region="전남광주통합특별시(광주)",
        address="전남광주통합특별시 동구 중앙로 302",
    ),
    School(
        eduOfficeCode="G10",
        eduOfficeName="대전광역시교육청",
        schoolCode="7430031",
        schoolName="대전고등학교",
        schoolKind="고등학교",
        region="대전광역시",
        address="대전광역시 중구 대흥로 110",
    ),
    School(
        eduOfficeCode="G10",
        eduOfficeName="대전광역시교육청",
        schoolCode="7451125",
        schoolName="한밭초등학교",
        schoolKind="초등학교",
        region="대전광역시",
        address="대전광역시 서구 문정로 221",
    ),
    School(
        eduOfficeCode="J10",
        eduOfficeName="경기도교육청",
        schoolCode="7530174",
        schoolName="수원고등학교",
        schoolKind="고등학교",
        region="경기도",
        address="경기도 수원시 팔달구 정조로 666-10",
    ),
    School(
        eduOfficeCode="M10",
        eduOfficeName="충청북도교육청",
        schoolCode="8000066",
        schoolName="청주고등학교",
        schoolKind="고등학교",
        region="충청북도",
        address="충청북도 청주시 흥덕구 사직대로 79",
    ),
]
