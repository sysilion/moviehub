굿즈조회 저장

롯데시네마 이벤트 목록 조회

LIST=$(curl -s 'https://www.lottecinema.co.kr/LCWS/Event/EventData.aspx' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryi2BeHTuMdz0O2qAx' \
  -H 'Cookie: WMONID=zg2nveSNnoo; TS01570c53=01337fb4697cbfc9354beaba0f02cb995087a6aa7e7f7b56bae544f43768a80f9e90995e00f7bc37ada713b0a97a17abcbd8487ff6; ASP.NET_SessionId=sqmu5tiarnj5swdfa0dxt4b5; AD_DMC=1; TS019bdbd5=01337fb4697cbfc9354beaba0f02cb995087a6aa7e7f7b56bae544f43768a80f9e90995e00f7bc37ada713b0a97a17abcbd8487ff6; cIntAkInfs=%25257B%252522domain%252522%25253A%252522https%25253A%25252F%25252Fmembers.lpoint.com%252522%25252C%252522flwNo%252522%25253A%2525229USjoIvGwW%252522%25252C%252522clntEncKey%252522%25253A%252522Qat7LCEv9qs%25252BylEv%252522%25257D' \
  -H 'DNT: 1' \
  -H 'Origin: https://www.lottecinema.co.kr' \
  -H 'Referer: https://www.lottecinema.co.kr/NLCMW/Event' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/87.0.4280.77 Mobile/15E148 Safari/604.1' \
  -d $'------WebKitFormBoundaryi2BeHTuMdz0O2qAx\r\nContent-Disposition: form-data; name="paramList"\r\n\r\n{"MethodName":"GetEventLists","channelType":"MW","osType":"I","osVersion":"Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/87.0.4280.77 Mobile/15E148 Safari/604.1","EventClassificationCode":"0","SearchText":"","CinemaID":"","PageNo":'${PAGE}$',"PageSize":40,"MemberNo":"0"}\r\n------WebKitFormBoundaryi2BeHTuMdz0O2qAx--\r\n' \
  --compressed)

response

{
  "Items": [
    {
      "EventID": "201010016926021",
      "EventName": "클래식 레미니선스 <이터널 선샤인>",
      "EventClassificationCode": "20",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.21",
      "ProgressEndDate": "2026.02.24",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/df0e49278fce49c1bfc04ac143c3225e.jpg",
      "ImageAlt": "클래식 레미니선스 <이터널 선샤인>",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 0,
      "RemainsDayCount": 47,
      "EventWinnerYN": 0,
      "EventSeq": 96,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "401010016926002",
      "EventName": "<시라트>개봉 전주 유료 프리미어 상영(일반포맷)",
      "EventClassificationCode": "40",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.18",
      "ProgressEndDate": "2026.01.18",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/6e0505014ebe48f59c35d8515f026f0c.jpg",
      "ImageAlt": "<시라트>개봉 전주 유료 프리미어 상영(일반포맷)",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 0,
      "RemainsDayCount": 10,
      "EventWinnerYN": 0,
      "EventSeq": 95,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "201010016926026",
      "EventName": "<더 퍼스트 슬램덩크>광음 키링 증정 이벤트",
      "EventClassificationCode": "20",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.14",
      "ProgressEndDate": "2026.01.20",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/2691b15001344192a020037e59e1050e.jpg",
      "ImageAlt": "<더 퍼스트 슬램덩크>광음 키링 증정 이벤트",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 0,
      "RemainsDayCount": 12,
      "EventWinnerYN": 0,
      "EventSeq": 94,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "201010016926027",
      "EventName": "<하트맨>시그니처 아트카드 증정이벤트",
      "EventClassificationCode": "20",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.14",
      "ProgressEndDate": "2026.01.27",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/4e4a5c06e50e4e0580eb3decb1dd4eff.jpg",
      "ImageAlt": "<하트맨>시그니처 아트카드 증정이벤트",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 0,
      "RemainsDayCount": 19,
      "EventWinnerYN": 0,
      "EventSeq": 93,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "401010016926003",
      "EventName": "<고고다이노>개봉 전 프리미어 상영회",
      "EventClassificationCode": "40",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.10",
      "ProgressEndDate": "2026.01.11",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/0195077d7ae743ea8ad9dbe4fe70fe70.jpg",
      "ImageAlt": "<고고다이노>개봉 전 프리미어 상영회",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 1,
      "RemainsDayCount": 3,
      "EventWinnerYN": 0,
      "EventSeq": 92,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "401010016926001",
      "EventName": "<신비아파트>프리미어 상영회",
      "EventClassificationCode": "40",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.10",
      "ProgressEndDate": "2026.01.11",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/a98e1c5f075e4005a03fec3c9feb3afc.jpg",
      "ImageAlt": "<신비아파트>프리미어 상영회",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 1,
      "RemainsDayCount": 3,
      "EventWinnerYN": 0,
      "EventSeq": 91,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "201010016926029",
      "EventName": "<주술회전>6주차 주말증정이벤트",
      "EventClassificationCode": "20",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.10",
      "ProgressEndDate": "2026.01.13",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/88b232174d5a439f99785c2ef567e3d8.jpg",
      "ImageAlt": "<주술회전>6주차 주말증정이벤트",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 0,
      "RemainsDayCount": 5,
      "EventWinnerYN": 0,
      "EventSeq": 90,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "201010016926020",
      "EventName": "<마이 선샤인>1주차 주말 증정이벤트",
      "EventClassificationCode": "20",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.10",
      "ProgressEndDate": "2026.01.16",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/09097a0fe79d4cef9c9fdab98ffe9830.jpg",
      "ImageAlt": "<마이 선샤인>1주차 주말 증정이벤트",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 0,
      "RemainsDayCount": 8,
      "EventWinnerYN": 0,
      "EventSeq": 89,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "201010016926019",
      "EventName": "<뽀로로 극장판> 5주차 증정이벤트",
      "EventClassificationCode": "20",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.10",
      "ProgressEndDate": "2026.01.30",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/8d98fb295989454d8f4e6877b1c1e127.jpg",
      "ImageAlt": "<뽀로로 극장판> 5주차 증정이벤트",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 0,
      "RemainsDayCount": 22,
      "EventWinnerYN": 0,
      "EventSeq": 88,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "201010016926028",
      "EventName": "<스폰지밥 무비>2주차 주말증정이벤트",
      "EventClassificationCode": "20",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.10",
      "ProgressEndDate": "2026.01.30",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/eb043f0b61cc48d789ff70f142f04544.jpg",
      "ImageAlt": "<스폰지밥 무비>2주차 주말증정이벤트",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 0,
      "RemainsDayCount": 22,
      "EventWinnerYN": 0,
      "EventSeq": 87,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "201010016926025",
      "EventName": "<오늘 밤~>3주차 주말증정이벤트",
      "EventClassificationCode": "20",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.09",
      "ProgressEndDate": "2026.01.13",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/681d64c4e16a436594739595743a9f47.jpg",
      "ImageAlt": "<오늘 밤~>3주차 주말증정이벤트",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 0,
      "RemainsDayCount": 5,
      "EventWinnerYN": 0,
      "EventSeq": 86,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "201010016926009",
      "EventName": "<만약에 우리>2주차 증정이벤트",
      "EventClassificationCode": "20",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.08",
      "ProgressEndDate": "2026.01.13",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/51a30db222664a048b2f9e6a97106a6a.jpg",
      "ImageAlt": "<만약에 우리>2주차 증정이벤트",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 0,
      "RemainsDayCount": 5,
      "EventWinnerYN": 0,
      "EventSeq": 85,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "201010016926007",
      "EventName": "<톰과 제리>2주차 증정이벤트",
      "EventClassificationCode": "20",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.08",
      "ProgressEndDate": "2026.01.13",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/d5b94afefe5949549550bc97b3f87a05.jpg",
      "ImageAlt": "<톰과 제리>2주차 증정이벤트",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 0,
      "RemainsDayCount": 5,
      "EventWinnerYN": 0,
      "EventSeq": 84,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "401070016926011",
      "EventName": "<스폰지밥 무비>스페셜 상영회(1/10~11)",
      "EventClassificationCode": "40",
      "EventTypeCode": "107",
      "EventTypeName": "무대인사",
      "ProgressStartDate": "2026.01.10",
      "ProgressEndDate": "2026.01.11",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/c7fc536511694268bc741fcae0ef2836.jpg",
      "ImageAlt": "<스폰지밥 무비>스페셜 상영회(1/10~11)",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 1,
      "RemainsDayCount": 3,
      "EventWinnerYN": 0,
      "EventSeq": 83,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "401070016926012",
      "EventName": "<마이 선샤인>스노우볼뱃지상영회(1/11일)",
      "EventClassificationCode": "40",
      "EventTypeCode": "107",
      "EventTypeName": "무대인사",
      "ProgressStartDate": "2026.01.11",
      "ProgressEndDate": "2026.01.11",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/1d290614b92a41469ccd7132ad63645d.jpg",
      "ImageAlt": "<마이 선샤인>스노우볼뱃지상영회(1/11일)",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 1,
      "RemainsDayCount": 3,
      "EventWinnerYN": 0,
      "EventSeq": 82,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "401070014726001",
      "EventName": "<주토피아 2> 팬심 자랑 상영회",
      "EventClassificationCode": "40",
      "EventTypeCode": "107",
      "EventTypeName": "무대인사",
      "ProgressStartDate": "2026.01.11",
      "ProgressEndDate": "2026.01.11",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/8639ace1ec2249f890af9f97f4ccf9de.jpg",
      "ImageAlt": "<주토피아 2> 팬심 자랑 상영회",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 1,
      "RemainsDayCount": 3,
      "EventWinnerYN": 0,
      "EventSeq": 81,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "401070016926010",
      "EventName": "<뽀로로 극장판>5주차 무대인사",
      "EventClassificationCode": "40",
      "EventTypeCode": "107",
      "EventTypeName": "무대인사",
      "ProgressStartDate": "2026.01.10",
      "ProgressEndDate": "2026.01.11",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/83b6c1d76004474d9590e49f4d64b765.jpg",
      "ImageAlt": "<뽀로로 극장판>5주차 무대인사",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 1,
      "RemainsDayCount": 3,
      "EventWinnerYN": 0,
      "EventSeq": 80,
      "EventCntnt": "",
      "EventNtc": ""
    },
    {
      "EventID": "201010016926010",
      "EventName": "<척의 일생>3주차 증정이벤트",
      "EventClassificationCode": "20",
      "EventTypeCode": "101",
      "EventTypeName": "정보전달형(공지)",
      "ProgressStartDate": "2026.01.07",
      "ProgressEndDate": "2026.01.13",
      "ImageUrl": "http://cf.lottecinema.co.kr//Media/Event/e2367963a4ac445a9849b03a17d08d01.jpg",
      "ImageAlt": "<척의 일생>3주차 증정이벤트",
      "ImageDivisionCode": 20,
      "CinemaID": "",
      "CinemaName": "",
      "CinemaAreaCode": "",
      "CinemaAreaName": "",
      "DevTemplateYN": 0,
      "CloseNearYN": 0,
      "RemainsDayCount": 5,
      "EventWinnerYN": 0,
      "EventSeq": 79,
      "EventCntnt": "",
      "EventNtc": ""
    }
      ],
  "TotalCount": 96,
  "IsOK": "true",
  "ResultMessage": "SUCCESS",
  "ResultCode": null,
  "EventResultYn": null
}



롯데시네마 이벤트 세부정보 조회

data=$(curl -s 'https://www.lottecinema.co.kr/LCWS/Event/EventData.aspx' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: en-US,en;q=0.9,ko-KR;q=0.8,ko;q=0.7' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: multipart/form-data; boundary=----WebKitFormBoundarywmwPwhv8uTBaAdsh' \
  -H 'DNT: 1' \
  -H 'Origin: https://www.lottecinema.co.kr' \
  -H 'Referer: https://www.lottecinema.co.kr/NLCMW/Event/EventTemplateInfo?eventId=201010016923143' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/87.0.4280.77 Mobile/15E148 Safari/604.1' \
  -H 'sec-gpc: 1' \
  -d $'------WebKitFormBoundarywmwPwhv8uTBaAdsh
Content-Disposition: form-data; name="paramList"

{"MethodName":"GetInfomationDeliveryEventDetail","channelType":"MW","osType":"I","osVersion":"Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/87.0.4280.77 Mobile/15E148 Safari/604.1","EventID":"'${EVENT_ID}$'"}
------WebKitFormBoundarywmwPwhv8uTBaAdsh--' \
        --compressed)

response

{
  "InfomationDeliveryEventDetail": [
    {
      "ButtonSetting": [],
      "JoinStatus": [],
      "GoodsGiftItems": [],
      "EventClassificationCode": "20",
      "EventID": "201010016926026",
      "EventName": "<더 퍼스트 슬램덩크>광음 키링 증정 이벤트",
      "ProgressStartDate": "2026-01-14",
      "ProgressEndDate": "2026-01-20",
      "WinnerAnnouncmentDate": "",
      "ImgUrl": "http://cf.lottecinema.co.kr//Media/Event/892404028c4441fa8d2f7cd25ea7d9d3.jpg",
      "ImgAlt": "<더 퍼스트 슬램덩크>광음 키링 증정 이벤트",
      "ImageDivisionCode": 20,
      "ImageGameTypeDivisionCode": null,
      "EventContents": "",
      "EventNotice": "",
      "WinnerNotice": null,
      "CinemaID": "0",
      "CinemaName": "",
      "EventProgressDivisionCode": 10,
      "EventMovieURL": "",
      "EventMovieImageURL": "",
      "EventMovieImageAlt": "<더 퍼스트 슬램덩크>광음 키링 증정 이벤트",
      "ListImgUrl": "http://cf.lottecinema.co.kr//Media/Event/2691b15001344192a020037e59e1050e.jpg",
      "ListImgAlt": "<더 퍼스트 슬램덩크>광음 키링 증정 이벤트",
      "GoodsShowYN": "0",
      "InformationOfferingAgreementYN": 0,
      "InformationOfferingAgreementContents": ""
    }
  ],
  "IsOK": "true",
  "ResultMessage": "SUCCESS",
  "ResultCode": null,
  "EventResultYn": null
}


롯데시네마 이벤트 굿즈 조회

goods=$(curl -s 'https://www.lottecinema.co.kr/LCWS/Event/EventData.aspx' \
  -H 'Accept: application/json, text/plain, */*' \
  -H 'Accept-Language: en-US,en;q=0.9' \
  -H 'Connection: keep-alive' \
  -H 'Content-Type: multipart/form-data; boundary=----WebKitFormBoundarybnui9W42liz3d0zP' \
  -H 'DNT: 1' \
  -H 'Origin: https://www.lottecinema.co.kr' \
  -H 'Referer: https://www.lottecinema.co.kr/NLCMW/Event/EventTemplateInfo?eventId='${EVENT_ID} \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'User-Agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36' \
  -H 'sec-ch-ua: "Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"' \
  -H 'sec-ch-ua-mobile: ?1' \
  -H 'sec-ch-ua-platform: "Android"' \
  -d $'------WebKitFormBoundarybnui9W42liz3d0zP
Content-Disposition: form-data; name="paramList"

{"MethodName":"GetCinemaGoods","channelType":"MW","osType":"A","osVersion":"Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36","EventID":"'${EVENT_ID}'","GiftID":"'${GIFT_ID}'"}
------WebKitFormBoundarybnui9W42liz3d0zP--' \
  --compressed)

response

{
  "CinemaDivisions": [
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0001",
      "GroupNameKR": "서울",
      "GroupNameUS": "Seoul",
      "SortSequence": 1,
      "CinemaCount": 10
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "GroupNameKR": "경기/인천",
      "GroupNameUS": "Gyeonggi/Incheon",
      "SortSequence": 2,
      "CinemaCount": 15
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0003",
      "GroupNameKR": "충청/대전",
      "GroupNameUS": "Chungcheong/Daejeon",
      "SortSequence": 3,
      "CinemaCount": 1
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0004",
      "GroupNameKR": "전라/광주",
      "GroupNameUS": "Cholla/Gwangju",
      "SortSequence": 4,
      "CinemaCount": 3
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0005",
      "GroupNameKR": "경북/대구",
      "GroupNameUS": "Gyeongbuk/Daegu",
      "SortSequence": 5,
      "CinemaCount": 3
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0101",
      "GroupNameKR": "경남/부산/울산",
      "GroupNameUS": "Gyeongnam/Busan/Ulsan",
      "SortSequence": 6,
      "CinemaCount": 8
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0006",
      "GroupNameKR": "강원",
      "GroupNameUS": "Gangwon",
      "SortSequence": 7,
      "CinemaCount": 1
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0007",
      "GroupNameKR": "제주",
      "GroupNameUS": "Jeju",
      "SortSequence": 8,
      "CinemaCount": 0
    }
  ],
  "CinemaDivisionGoods": [
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0001",
      "CinemaID": "1004",
      "CinemaNameKR": "건대입구",
      "CinemaNameUS": "Konkuk Univ",
      "SortSequence": 6,
      "Cnt": 260,
      "DetailDivisionNameKR": "서울",
      "DetailDivisionNameUS": "Seoul"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0001",
      "CinemaID": "1009",
      "CinemaNameKR": "김포공항",
      "CinemaNameUS": "Gimpo Int'l Airport",
      "SortSequence": 7,
      "Cnt": 170,
      "DetailDivisionNameKR": "서울",
      "DetailDivisionNameUS": "Seoul"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0001",
      "CinemaID": "1003",
      "CinemaNameKR": "노원",
      "CinemaNameUS": "Nowon",
      "SortSequence": 8,
      "Cnt": 210,
      "DetailDivisionNameKR": "서울",
      "DetailDivisionNameUS": "Seoul"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0001",
      "CinemaID": "1023",
      "CinemaNameKR": "도곡",
      "CinemaNameUS": "Dogok",
      "SortSequence": 9,
      "Cnt": 80,
      "DetailDivisionNameKR": "서울",
      "DetailDivisionNameUS": "Seoul"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0001",
      "CinemaID": "1017",
      "CinemaNameKR": "독산",
      "CinemaNameUS": "Doksan",
      "SortSequence": 10,
      "Cnt": 40,
      "DetailDivisionNameKR": "서울",
      "DetailDivisionNameUS": "Seoul"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0001",
      "CinemaID": "1007",
      "CinemaNameKR": "신림",
      "CinemaNameUS": "Sillim",
      "SortSequence": 18,
      "Cnt": 260,
      "DetailDivisionNameKR": "서울",
      "DetailDivisionNameUS": "Seoul"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0001",
      "CinemaID": "1002",
      "CinemaNameKR": "영등포",
      "CinemaNameUS": "Yeongdeungpo",
      "SortSequence": 20,
      "Cnt": 170,
      "DetailDivisionNameKR": "서울",
      "DetailDivisionNameUS": "Seoul"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0001",
      "CinemaID": "1016",
      "CinemaNameKR": "월드타워",
      "CinemaNameUS": "WorldTower",
      "SortSequence": 22,
      "Cnt": 340,
      "DetailDivisionNameKR": "서울",
      "DetailDivisionNameUS": "Seoul"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0001",
      "CinemaID": "1021",
      "CinemaNameKR": "은평(롯데몰)",
      "CinemaNameUS": "Eunpyeong",
      "SortSequence": 23,
      "Cnt": 100,
      "DetailDivisionNameKR": "서울",
      "DetailDivisionNameUS": "Seoul"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0001",
      "CinemaID": "1008",
      "CinemaNameKR": "청량리",
      "CinemaNameUS": "Cheongnyangni",
      "SortSequence": 25,
      "Cnt": 230,
      "DetailDivisionNameKR": "서울",
      "DetailDivisionNameUS": "Seoul"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3025",
      "CinemaNameKR": "광명아울렛",
      "CinemaNameUS": "Gwangmyeong Outlet",
      "SortSequence": 7,
      "Cnt": 50,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3026",
      "CinemaNameKR": "구리아울렛",
      "CinemaNameUS": "Guri Outlet",
      "SortSequence": 9,
      "Cnt": 70,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3017",
      "CinemaNameKR": "병점",
      "CinemaNameUS": "Byeongjeom",
      "SortSequence": 14,
      "Cnt": 30,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3011",
      "CinemaNameKR": "부천(신중동역)",
      "CinemaNameUS": "Bucheon",
      "SortSequence": 15,
      "Cnt": 50,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3050",
      "CinemaNameKR": "부평갈산",
      "CinemaNameUS": "Bupyeong Galsan",
      "SortSequence": 20,
      "Cnt": 30,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3008",
      "CinemaNameKR": "부평역사",
      "CinemaNameUS": "Bupyeong Sation",
      "SortSequence": 21,
      "Cnt": 60,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3031",
      "CinemaNameKR": "산본피트인",
      "CinemaNameUS": "Sanbon Fitin",
      "SortSequence": 25,
      "Cnt": 80,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3041",
      "CinemaNameKR": "성남중앙(신흥역)",
      "CinemaNameUS": "Seongnam Jungang",
      "SortSequence": 28,
      "Cnt": 110,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3044",
      "CinemaNameKR": "수지",
      "CinemaNameUS": "Suji",
      "SortSequence": 34,
      "Cnt": 90,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3004",
      "CinemaNameKR": "안산",
      "CinemaNameUS": "Ansan",
      "SortSequence": 37,
      "Cnt": 70,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3007",
      "CinemaNameKR": "안양(안양역)",
      "CinemaNameUS": "Anyang",
      "SortSequence": 40,
      "Cnt": 80,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3039",
      "CinemaNameKR": "용인기흥",
      "CinemaNameUS": "Yongin Giheung",
      "SortSequence": 44,
      "Cnt": 60,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3037",
      "CinemaNameKR": "위례",
      "CinemaNameUS": "Wirye",
      "SortSequence": 46,
      "Cnt": 70,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3034",
      "CinemaNameKR": "파주운정",
      "CinemaNameUS": "Paju Unjeong",
      "SortSequence": 55,
      "Cnt": 80,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0002",
      "CinemaID": "3018",
      "CinemaNameKR": "평촌(범계역)",
      "CinemaNameUS": "Pyeongchon",
      "SortSequence": 57,
      "Cnt": 240,
      "DetailDivisionNameKR": "경기/인천",
      "DetailDivisionNameUS": "Gyeonggi/Incheon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0003",
      "CinemaID": "4007",
      "CinemaNameKR": "청주용암",
      "CinemaNameUS": "Cheongju Yongam",
      "SortSequence": 12,
      "Cnt": 20,
      "DetailDivisionNameKR": "충청/대전",
      "DetailDivisionNameUS": "Chungcheong/Daejeon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0004",
      "CinemaID": "6009",
      "CinemaNameKR": "군산몰",
      "CinemaNameUS": "Gunsan Mall",
      "SortSequence": 5,
      "Cnt": 60,
      "DetailDivisionNameKR": "전라/광주",
      "DetailDivisionNameUS": "Cholla/Gwangju"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0004",
      "CinemaID": "6004",
      "CinemaNameKR": "수완(아울렛)",
      "CinemaNameUS": "Suwan",
      "SortSequence": 6,
      "Cnt": 60,
      "DetailDivisionNameKR": "전라/광주",
      "DetailDivisionNameUS": "Cholla/Gwangju"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0004",
      "CinemaID": "6002",
      "CinemaNameKR": "전주(백화점)",
      "CinemaNameUS": "Jeonju",
      "SortSequence": 8,
      "Cnt": 40,
      "DetailDivisionNameKR": "전라/광주",
      "DetailDivisionNameUS": "Cholla/Gwangju"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0005",
      "CinemaID": "5012",
      "CinemaNameKR": "대구광장",
      "CinemaNameUS": "Daegu Plaza",
      "SortSequence": 8,
      "Cnt": 20,
      "DetailDivisionNameKR": "경북/대구",
      "DetailDivisionNameUS": "Gyeongbuk/Daegu"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0005",
      "CinemaID": "5016",
      "CinemaNameKR": "상인",
      "CinemaNameUS": "Sangin",
      "SortSequence": 13,
      "Cnt": 60,
      "DetailDivisionNameKR": "경북/대구",
      "DetailDivisionNameUS": "Gyeongbuk/Daegu"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0005",
      "CinemaID": "5004",
      "CinemaNameKR": "성서",
      "CinemaNameUS": "Seongseo",
      "SortSequence": 15,
      "Cnt": 60,
      "DetailDivisionNameKR": "경북/대구",
      "DetailDivisionNameUS": "Gyeongbuk/Daegu"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0006",
      "CinemaID": "7003",
      "CinemaNameKR": "원주무실",
      "CinemaNameUS": "Wonju Musil",
      "SortSequence": 5,
      "Cnt": 180,
      "DetailDivisionNameKR": "강원",
      "DetailDivisionNameUS": "Gangwon"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0101",
      "CinemaID": "2009",
      "CinemaNameKR": "광복",
      "CinemaNameUS": "Gwangbok",
      "SortSequence": 5,
      "Cnt": 190,
      "DetailDivisionNameKR": "경남/부산/울산",
      "DetailDivisionNameUS": "Gyeongnam/Busan/Ulsan"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0101",
      "CinemaID": "5015",
      "CinemaNameKR": "김해부원",
      "CinemaNameUS": "Gimhae Buwon",
      "SortSequence": 7,
      "Cnt": 30,
      "DetailDivisionNameKR": "경남/부산/울산",
      "DetailDivisionNameUS": "Gyeongnam/Busan/Ulsan"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0101",
      "CinemaID": "2007",
      "CinemaNameKR": "동래",
      "CinemaNameUS": "Dongnae",
      "SortSequence": 12,
      "Cnt": 70,
      "DetailDivisionNameKR": "경남/부산/울산",
      "DetailDivisionNameUS": "Gyeongnam/Busan/Ulsan"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0101",
      "CinemaID": "2004",
      "CinemaNameKR": "부산본점",
      "CinemaNameUS": "Busan",
      "SortSequence": 16,
      "Cnt": 90,
      "DetailDivisionNameKR": "경남/부산/울산",
      "DetailDivisionNameUS": "Gyeongnam/Busan/Ulsan"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0101",
      "CinemaID": "2006",
      "CinemaNameKR": "센텀시티",
      "CinemaNameUS": "Centumcity",
      "SortSequence": 21,
      "Cnt": 70,
      "DetailDivisionNameKR": "경남/부산/울산",
      "DetailDivisionNameUS": "Gyeongnam/Busan/Ulsan"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0101",
      "CinemaID": "5001",
      "CinemaNameKR": "울산(백화점)",
      "CinemaNameUS": "Ulsan",
      "SortSequence": 25,
      "Cnt": 60,
      "DetailDivisionNameKR": "경남/부산/울산",
      "DetailDivisionNameUS": "Gyeongnam/Busan/Ulsan"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0101",
      "CinemaID": "5017",
      "CinemaNameKR": "진주혁신(롯데몰)",
      "CinemaNameUS": "Jinju Innovation City",
      "SortSequence": 28,
      "Cnt": 40,
      "DetailDivisionNameKR": "경남/부산/울산",
      "DetailDivisionNameUS": "Gyeongnam/Busan/Ulsan"
    },
    {
      "DivisionCode": 1,
      "DetailDivisionCode": "0101",
      "CinemaID": "5002",
      "CinemaNameKR": "창원",
      "CinemaNameUS": "Changwon",
      "SortSequence": 30,
      "Cnt": 110,
      "DetailDivisionNameKR": "경남/부산/울산",
      "DetailDivisionNameUS": "Gyeongnam/Busan/Ulsan"
    }
  ],
  "IsOK": "true",
  "ResultMessage": "SUCCESS",
  "ResultCode": null,
  "EventResultYn": null
}





이벤트 조회시 이름에 '증정, 뱃지, 아트카드, artcard, 무비티켓, 키링' 등 해당되는게 있으면 해당 이벤트는 굿즈를 줄거라고 추측.

### 자동 탐색 로직 (Implemented)

`src/collectors/lotte.py`에 구현된 `discover_new_events` 메서드는 다음과 같은 방식으로 신규 이벤트와 굿즈를 탐색합니다:

1.  **기준점 설정**: DB에 저장된 마지막 `EventID`와 `GiftID`를 로드합니다.
2.  **순차적 스캔**:
    *   **이벤트**: 마지막 `EventID` + 1 부터 시작하여 **20개**의 잠재적 번호를 조회합니다.
    *   **굿즈**: 유효한 이벤트가 발견되면, 마지막 `GiftID` 부터 시작하여 **50개**의 번호를 순차적으로 대입해봅니다.
3.  **매칭 및 저장**:
    *   이벤트 상세 정보가 존재하고, 해당 이벤트 ID와 테스트 중인 굿즈 ID로 재고 조회 API(`GetCinemaGoods`) 호출 성공 시(응답에 `CinemaDivisionGoods` 존재) 유효한 매칭으로 판단합니다.
    *   매칭된 정보는 즉시 DB(`Event`, `Inventory`, `InventoryHistory`)에 저장됩니다.

이 로직은 `Scheduler`의 `main_discovery_job`에 의해 주기적으로 실행되어 신규 이벤트를 자동으로 감지합니다.


