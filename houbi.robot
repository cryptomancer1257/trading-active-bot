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
${indicators}        []
${BROWSER}           chrome

*** Tasks ***
ScreenShot Image not login
    # Parse timeframe từ JSON string thành list
    ${parsed_timeframes}=    Evaluate    json.loads('''${timeframe}''')    json
    Set Global Variable    ${parsed_timeframes}
    
    ${options}=    Evaluate    {'arguments': ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--window-size=1920,1080']}

    ${url}=    Set Variable    https://www.htx.com/trade/${trading_pair} 

    TRY
        Open Available Browser
        ...    ${url}
        ...    browser_selection=chrome
        ...    options=${options}
    EXCEPT    AS    ${error}
        Log    Failed to open browser: ${error}    level=ERROR
        Fail    Browser initialization failed
    END

    Sleep    3s 
    Handle Cookie Popup Houbi
    Sleep    2s
    
    # Debug trước khi thao tác
    Debug HTX Page Structure
    
    # Đảm bảo ở main frame
    Unselect Frame If Active

    # Mở fullscreen trước khi thao tác indicators
    Click Fullscreen Houbi

    Load And Select Indicators Houbi

    Create Directory    screenshots

    FOR    ${tf}    IN    @{parsed_timeframes}
        Log    Chọn timeframe HTX: ${tf} level=INFO
        TRY
            # Ưu tiên chọn qua dropdown "Select Interval"
            Open Interval Dropdown Houbi
            Select Timeframe From Dropdown Houbi    ${tf}
            Sleep    3s
            
            ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
            ${filepath}=    Set Variable    screenshots/houbi_${trading_pair}_${tf}_${timestamp}.png
            Capture Page Screenshot    ${filepath}
            Append To File    screenshots/${session_id}_image.txt    ${filepath}\n
            Log    Đã chụp screenshot cho timeframe ${tf}: ${filepath}
            
        EXCEPT    AS    ${error}
            Log    Lỗi khi xử lý timeframe ${tf}: ${error}    level=ERROR
            ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
            ${error_filepath}=    Set Variable    screenshots/error_houbi_${trading_pair}_${tf}_${timestamp}.png
            Capture Page Screenshot    ${error_filepath}
            Continue For Loop
        END
    END
*** Keywords ***
Click Fullscreen Houbi
    # Click đúng nút fullscreen với selector chi tiết
    ${fullscreen_btn}=    Set Variable    //div[@class="fullscreen-container"]/div[@class="el-tooltip fullscreen"]
    Wait Until Element Is Visible    ${fullscreen_btn}    8s
    Scroll Element Into View    ${fullscreen_btn}
    Click Element    ${fullscreen_btn}
    Sleep    2s

*** Keywords ***
Unselect Frame If Active
    TRY
        Unselect Frame
        Log    Đã trở về main frame
    EXCEPT
        Log    Đã ở main frame
    END

Debug HTX Page Structure
    Log    Đang debug cấu trúc trang HTX...
    Capture Page Screenshot    screenshots/debug_htx_structure.png
    
    # Kiểm tra các phần tử quan trọng
    ${elements_to_check}=    Create List
    ...    xpath=//div[contains(@class,"toolbar-content")]//div[contains(@class,"indicator-container")]
    ...    css:div.toolbar-content div.indicator-container
    
    FOR    ${selector}    IN    @{elements_to_check}
        ${found}=    Run Keyword And Return Status    Page Should Contain Element    ${selector}
        IF    ${found}
            Log    Tìm thấy: ${selector}
        ELSE
            Log    Không tìm thấy: ${selector}    level=WARN
        END
    END

Handle Cookie Popup Houbi
    TRY
        ${accept_buttons}=    Get WebElements    xpath=//button[contains(., 'Accept') or contains(., 'AGREE') or contains(., 'Allow')]
        IF    ${accept_buttons}
            Click Element    ${accept_buttons}[0]
            Log    Đã click Accept cookies
            Sleep    2s
        END
    EXCEPT
        Log    Không tìm thấy cookie popup hoặc đã xử lý
    END

Try Switch To Chart Iframe Houbi
    # Nhiều sàn nhúng TradingView
    ${iframes}=    Create List
    ...    css:iframe[src*='tradingview']
    ...    xpath=//iframe[contains(@src, 'tradingview')]
    ...    xpath=//iframe[contains(@src, 'embed')]
    ${switched}=    Set Variable    ${False}
    FOR    ${ifr}    IN    @{iframes}
        ${found}=    Run Keyword And Return Status    Wait Until Page Contains Element    ${ifr}    5s
        IF    ${found}
            Select Frame    ${ifr}
            ${switched}=    Set Variable    ${True}
            BREAK
        END
    END
    IF    not ${switched}
        Log    Không thấy iframe chart. Tiếp tục trên DOM chính    level=WARN
    END

Load And Select Indicators Houbi
    # Đảm bảo ở main frame trước khi tìm indicators
    Unselect Frame If Active

    Log    Đang Select Indicators Houbi 1    level=WARN
    
    # Nút Indicators có thể mở danh sách indicators trên HTX/TradingView
    ${indicator_selectors}=    Create List
    ...    xpath=//div[contains(@class,"toolbar-content")]//div[contains(@class,"indicator-container")]
    ...    css:div.toolbar-content div.indicator-container

    ${found_btn}=    Set Variable    ${False}
    FOR    ${sel}    IN    @{indicator_selectors}
        ${ok}=    Run Keyword And Return Status    Wait Until Page Contains Element    ${sel}    5s
        IF    ${ok}
            Log    Tìm thấy nút indicators với selector: ${sel}    level=WARN
            Scroll Element Into View    ${sel}
            Sleep    1s
            Click Element    ${sel}
            ${found_btn}=    Set Variable    ${True}
            Sleep    3s
            BREAK
        END
    END

    Log    Đang Select Indicators Houbi 2    level=WARN

    Run Keyword If    '${indicators}' not in ['NONE', '', '[]']    Select Indicators Dialog

Select Indicators Dialog

    Wait Until Page Contains Element    css:iframe[id^="tradingview_"]    10s
    Select Frame    css:iframe[id^="tradingview_"]

    # Parse indicators từ JSON string thành list
    ${parsed_indicators}=    Evaluate    json.loads('''${indicators}''')    json
    
    Log    Đang chọn các indicators: ${parsed_indicators}    level=WARN
    
    FOR    ${indicator}    IN    @{parsed_indicators}
        ${indicator_clean}=    Strip String    ${indicator}
        Log    Đang tìm indicator: ${indicator_clean}    level=WARN
        
        # Các selector để tìm indicator trong dialog
        ${indicator_selectors}=    Create List
        ...    xpath=//*[contains(text(), '${indicator_clean}')]
        ...    xpath=//div[contains(@class, 'item') and contains(., '${indicator_clean}')]
        ...    xpath=//span[contains(text(), '${indicator_clean}')]
        ...    xpath=//button[contains(., '${indicator_clean}')]
        ...    xpath=//li[contains(., '${indicator_clean}')]
        
        ${indicator_found}=    Set Variable    ${False}
        FOR    ${selector}    IN    @{indicator_selectors}
            ${found}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${selector}    3s
            IF    ${found}
                Log    ✅ Tìm thấy indicator '${indicator_clean}' với selector: ${selector}   level=WARN
                Scroll Element Into View    ${selector}
                ${element}=    Get WebElement    ${selector}
                Execute JavaScript    arguments[0].style.border='2px solid green';    ARGUMENTS    ${element}
                Sleep    0.5s
                
                Click Element    ${selector}
                Log    ✅ Đã chọn indicator: ${indicator_clean}    level=WARN
                ${indicator_found}=    Set Variable    ${True}
                Sleep    1s
                BREAK
            END
        END
        
        IF    not ${indicator_found}
            Log    ❌ Không tìm thấy indicator: ${indicator_clean}    level=WARN
        END
    END
    
    # Đóng dialog sau khi chọn indicators
    ${close_buttons}=    Create List
    ...    css:button[data-name="close-indicator-dialog"]
    ...    css:.dialog-close
    ...    xpath=//button[contains(@class, 'close')]
    ...    css:button[aria-label*="close" i]
    
    FOR    ${close_selector}    IN    @{close_buttons}
        ${found}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${close_selector}    2s
        IF    ${found}
            Click Element    ${close_selector}
            Log    ✅ Đã đóng dialog indicators
            BREAK
        END
    END
    
    # Nếu không tìm thấy nút close, thử ESC
    Press Keys    None    ESC
    Sleep    1s

Normalize Timeframe For Houbi
    [Arguments]    ${tf}
    ${u}=    Convert To Uppercase    ${tf}
    ${label}=    Set Variable    ${tf}
    # Chuẩn hóa theo định dạng HTX
    IF    '${u}' == '1H'
        ${label}=    Set Variable    1h
    ELSE IF    '${u}' == '4H' 
        ${label}=    Set Variable    4h
    ELSE IF    '${u}' == '1D'
        ${label}=    Set Variable    1D
    ELSE IF    '${u}' == '1W'
        ${label}=    Set Variable    1W
    ELSE IF    '${u}' == '1M'
        ${label}=    Set Variable    1M
    END
    [Return]    ${label}    ${label}

Open Interval Dropdown Houbi
    Log    Đang mở dropdown timeframe HTX thật...
    Unselect Frame If Active
    
    ${dropdown_button}=    Set Variable    css:div.trading-chart__toolbar div.action-button

    Wait Until Element Is Visible    ${dropdown_button}    10s

    Scroll Element Into View    ${dropdown_button}
    Click Element    ${dropdown_button}
    Log    ✅ Đã click nút Time để mở dropdown

    # Chờ popup hiện ra
    Wait Until Page Contains Element    css:.interval-popover-container    5s
    Log    ✅ Dropdown interval HTX đã mở thành công


Select Timeframe From Dropdown Houbi
    [Arguments]    ${tf}
    ${label}    ${value}=    Normalize Timeframe For Houbi    ${tf}
    Log    Chọn timeframe trong dropdown HTX: ${tf} -> ${label}

    ${item_xpath}=    Set Variable    //div[contains(@class,"interval-popover-container")]//*[normalize-space(text())="${label}"]

    ${found}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${item_xpath}    5s
    IF    ${found}
        Scroll Element Into View    ${item_xpath}
        Click Element    ${item_xpath}
        Log    ✅ Đã chọn timeframe: ${label}
    ELSE
        Log    ❌ Không tìm thấy timeframe: ${label}    level=ERROR
        Capture Page Screenshot    screenshots/debug_timeframe_not_found_${tf}.png
        Fail    Không tìm thấy timeframe '${label}' trong dropdown HTX
    END

    Sleep    2s