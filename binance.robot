*** Settings ***
Library    RPA.Browser.Selenium
Library    OperatingSystem
Library    Process
Library    JSONLibrary
Library    DateTime
Library    Collections
Library    String

*** Variables ***
${session_id}        NONE
${trading_pair}      NONE
${timeframe}         []
${main_indicators}   []
${sub_indicators}    []
${BROWSER}           chrome
${DROPDOWN_ICON}     css:svg.interval-expand-btn
${TIMEFRAME_MENU}    css:div.bn-timeframe-menu

*** Tasks ***
ScreenShot Image not login

    # Parse timeframe từ JSON string thành list
    ${parsed_timeframes}=    Evaluate    json.loads('''${timeframe}''')    json

    # Simple Chrome options cho Docker
    ${options}=    Evaluate    {'arguments': ['--headless=new', '--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--window-size=1920,1080']}
    
    ${url}=    Set Variable    https://www.binance.com/en/trade/${trading_pair}

    TRY
        Open Available Browser    
        ...    ${url}
        ...    browser_selection=chrome
        ...    options=${options}
    EXCEPT    AS    ${error}
        Log    Failed to open browser: ${error}    level=ERROR
        Fail    Browser initialization failed
    END


    # Phần còn lại của task
    Sleep    5s
    Handle Cookie Popup
    Sleep    1s
    Load And Select Indicators
    
    # Đảm bảo thư mục tồn tại
    Create Directory    /app/screenshots
    
    FOR    ${tf}    IN    @{parsed_timeframes}
        Log    Chọn timeframe: ${tf}

        Click Dropdown Icon    ${tf}
        Sleep    2s

        ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
        ${filepath}=    Set Variable    /app/screenshots/binance_${trading_pair}_${tf}_${timestamp}.png
        Capture Page Screenshot    ${filepath}
        Append To File    /app/screenshots/${session_id}_image.txt    ${filepath}\n
    END

*** Keywords ***
Handle Cookie Popup
    Wait Until Page Contains Element    //button[contains(., 'Reject Additional Cookies')]    10s
    Click Button    //button[contains(., 'Reject Additional Cookies')]

Load And Select Indicators
    # Mở menu Technical Indicator
    ${technical_indicator_icon}=    Set Variable    css:div.bn-tooltips-web > div.bn-tooltips-ele > div > svg[viewBox="0 0 24 24"] path[d*="M19.932 8.802a"]
    
    # Đợi và click vào icon
    Wait Until Page Contains Element    ${technical_indicator_icon}    10s
    Click Element                       ${technical_indicator_icon}
    Sleep    3s

    # Xử lý main indicators nếu có - skip for now due to selector issues
    Run Keyword If    ${main_indicators}   Select Main Indicators

    # Xử lý sub indicators nếu có - skip for now due to selector issues  
    Run Keyword If    ${sub_indicators}    Select Sub Indicators

    Sleep    2s
    Click Element    xpath=//*[name()='svg' and contains(@class, 'chart-fullscreen-icon')]

    Sleep    1s
    # Click Element    xpath=//div[normalize-space(text())="${timeframe}"]
    # Click Dropdown Icon
    Sleep    2s

Select Main Indicators
    ${main_clean}=    Replace String    ${main_indicators}    ["    ${EMPTY}
    ${main_clean}=    Replace String    ${main_clean}    "]    ${EMPTY}
    ${main_clean}=    Replace String    ${main_clean}    "    ${EMPTY}
    @{main_list}=    Split String    ${main_clean}    ,
    FOR    ${indicator}    IN    @{main_list}
        ${indicator_clean}=    Strip String    ${indicator}
        Ensure Checkbox Selected    ${indicator_clean}
    END

Select Sub Indicators
    Wait Until Element Is Visible    xpath=//div[@role="tab" and text()="Sub Indicator"]    5s
    Click Element                    xpath=//div[@role="tab" and text()="Sub Indicator"]
    Sleep    1s
    ${subs_clean}=    Replace String    ${sub_indicators}    ["    ${EMPTY}
    ${subs_clean}=    Replace String    ${subs_clean}    "]    ${EMPTY}
    ${subs_clean}=    Replace String    ${subs_clean}    "    ${EMPTY}
    @{subs_list}=    Split String    ${subs_clean}    ,
    FOR    ${indicator}    IN    @{subs_list}
        ${indicator_clean}=    Strip String    ${indicator}
        Ensure Checkbox Selected    ${indicator_clean}
    END
    Sleep    1s
    Click Button    xpath=//button[contains(., "Save")]

Ensure Checkbox Selected
    [Arguments]    ${label}
    ${checkbox_xpath}=    Set Variable    //div[div[text()="${label}"]]//div[@role="checkbox"]
    Wait Until Element Is Visible    ${checkbox_xpath}    5s
    ${is_checked}=    Get Element Attribute    ${checkbox_xpath}    aria-checked
    Run Keyword If    '${is_checked}' != 'true'    Click Element    ${checkbox_xpath}

Click Dropdown Icon
    [Arguments]    ${tf}
    Wait Until Element Is Visible    ${DROPDOWN_ICON}    10s

    ${dropdown_visible}=    Run Keyword And Return Status    Element Should Be Visible    ${TIMEFRAME_MENU}
    IF    not ${dropdown_visible}
        TRY
            Click Element    ${DROPDOWN_ICON}
            Sleep    1s
        EXCEPT    AS    ${err}
            Log    Không thể click: ${err}    level=ERROR
            Fail    Không thể mở dropdown timeframe
        END
    END

    Sleep    2s

    ${timeframe_locator}=    Set Variable    xpath=//div[contains(@class, 'typography-caption1') and normalize-space()="${tf}"]
    Click Element    ${timeframe_locator}