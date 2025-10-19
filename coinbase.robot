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

    # Simple Chrome options cho Docker
    ${options}=    Evaluate    {'arguments': ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--window-size=1920,1080']}
    
    # Convert trading pair format from BTC_USDT to BTC-USD for Coinbase
    ${coinbase_pair}=    Replace String    ${trading_pair}    _    -
    ${url}=    Set Variable    https://www.coinbase.com/advanced-trade/spot/${coinbase_pair}

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
    Sleep    2s
    Open Full Screen Chart
    Sleep    2s

    # Debug Timeframes

    Load And Select Indicators
    
    # Đảm bảo thư mục tồn tại trong thư mục hiện tại
    Create Directory    screenshots
    
    FOR    ${tf}    IN    @{parsed_timeframes}
        Log    Chọn timeframe: ${tf}

        TRY
            Select Timeframe Directly    ${tf}
            Sleep    3s
            
            # Đợi chart load xong sau khi chọn timeframe
            Wait Until Page Contains Element    css:.chart-widget    10s
            
            ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
            ${filepath}=    Set Variable    screenshots/coinbase_${trading_pair}_${tf}_${timestamp}.png
            
            # Chụp ảnh chart cụ thể thay vì toàn trang
            Capture Element Screenshot    css:.chart-widget    ${filepath}
            Append To File    screenshots/${session_id}_image.txt    ${filepath}\n
            Log    Đã chụp screenshot cho timeframe ${tf}: ${filepath}
            
        EXCEPT    AS    ${error}
            Log    Lỗi khi xử lý timeframe ${tf}: ${error}    level=ERROR
            ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
            ${error_filepath}=    Set Variable    screenshots/error_coinbase_${trading_pair}_${tf}_${timestamp}.png
            Capture Page Screenshot    ${error_filepath}
            Log    Đã chụp screenshot lỗi: ${error_filepath}
            Continue For Loop
        END
    END

*** Keywords ***
Normalize Timeframe For Coinbase
    [Arguments]    ${tf}
    ${tf_upper}=    Convert To Uppercase    ${tf}
    
    # Mapping dựa trên cấu trúc HTML bạn cung cấp
    IF    '${tf_upper}' == '1H'
        ${label}=    Set Variable    1H
        ${value}=    Set Variable    60
        ${data_name}=    Set Variable    date-range-tab-60
    ELSE IF    '${tf_upper}' == '4H'
        ${label}=    Set Variable    4H
        ${value}=    Set Variable    240
        ${data_name}=    Set Variable    date-range-tab-240
    ELSE IF    '${tf_upper}' == '1D'
        ${label}=    Set Variable    1D
        ${value}=    Set Variable    1D
        ${data_name}=    Set Variable    date-range-tab-1D
    ELSE IF    '${tf_upper}' == '5D'
        ${label}=    Set Variable    5D
        ${value}=    Set Variable    5D
        ${data_name}=    Set Variable    date-range-tab-5D
    ELSE IF    '${tf_upper}' == '1M'
        ${label}=    Set Variable    1M
        ${value}=    Set Variable    1M
        ${data_name}=    Set Variable    date-range-tab-1M
    ELSE IF    '${tf_upper}' == '3M'
        ${label}=    Set Variable    3M
        ${value}=    Set Variable    3M
        ${data_name}=    Set Variable    date-range-tab-3M
    ELSE IF    '${tf_upper}' == '6M'
        ${label}=    Set Variable    6M
        ${value}=    Set Variable    6M
        ${data_name}=    Set Variable    date-range-tab-6M
    ELSE
        # fallback
        ${label}=    Set Variable    ${tf_upper}
        ${value}=    Set Variable    ${tf_upper}
        ${data_name}=    Set Variable    date-range-tab-${tf_upper}
    END
    
    [Return]    ${label}    ${value}    ${data_name}

Select Timeframe Directly
    [Arguments]    ${tf}

    ${label}    ${value}    ${data_name}=    Normalize Timeframe For Coinbase    ${tf}

    Log    Đang chọn timeframe: ${tf} -> label: ${label}, value: ${value}, data-name: ${data_name}

    Wait Until Page Contains Element    xpath=//div[@data-name="date-ranges-tabs"]    15s

    ${timeframe_selectors}=    Create List
    ...    xpath=//div[@data-name="date-ranges-tabs"]//button[@data-name="${data_name}"]
    ...    xpath=//div[@data-name="date-ranges-tabs"]//button[@value="${value}"]
    ...    xpath=//div[@data-name="date-ranges-tabs"]//button[@aria-label[contains(., "${label}")]]
    ...    xpath=//div[@data-name="date-ranges-tabs"]//button[@data-tooltip[contains(., "${label}")]]

    ${element_found}=    Set Variable    ${False}
    FOR    ${selector}    IN    @{timeframe_selectors}
        ${found}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${selector}    3s
        IF    ${found}
            Log    Tìm thấy timeframe với selector: ${selector}
            Scroll Element Into View    ${selector}
            Sleep    0.5s
            Click Element    ${selector}
            ${element_found}=    Set Variable    ${True}
            BREAK
        END
    END

    IF    not ${element_found}
        Log    Không thể tìm thấy timeframe "${tf}"    level=ERROR
        Capture Page Screenshot    screenshots/debug_timeframe_${tf}.png
        Fail    Không thể tìm thấy timeframe "${tf}"
    END

    Sleep    2s


Debug Timeframes
    Wait Until Page Contains Element    xpath=//div[@data-name="date-ranges-tabs"]    10s
    ${buttons}=    Get WebElements    xpath=//div[@data-name="date-ranges-tabs"]//button
    FOR    ${b}    IN    @{buttons}
        ${txt}=    Get Text    ${b}
        ${val}=    Get Element Attribute    ${b}    value
        ${name}=   Get Element Attribute    ${b}    data-name
        Log    Button -> text="${txt}", value="${val}", data-name="${name}"
    END

Handle Cookie Popup
    # Coinbase có thể có cookie popup khác với Binance
    ${cookie_popup}=    Run Keyword And Return Status    Wait Until Page Contains Element    //button[contains(., 'Accept')]    5s
    IF    ${cookie_popup}
        Click Button    //button[contains(., 'Accept')]
        Sleep    1s
    END
    
    # Xử lý popup khác nếu có
    ${other_popup}=    Run Keyword And Return Status    Wait Until Page Contains Element    //button[contains(., 'Continue')]    3s
    IF    ${other_popup}
        Click Button    //button[contains(., 'Continue')]
        Sleep    1s
    END

Open Full Screen Chart
    ${expand_button}=    Run Keyword And Return Status    Wait Until Page Contains Element    css:button[data-testid="expand-collapse-button"]    5s
    IF    ${expand_button}
        Click Element    css:button[data-testid="expand-collapse-button"]
        Log    Đã mở chế độ full screen chart
    ELSE
        Log    Không tìm thấy nút full screen    level=WARN
    END

Load And Select Indicators
    Log    🔍 Đang tìm nút Indicators & Strategies với độ chính xác cao     level=WARN

    # Đợi trang load hoàn toàn
    Sleep    5s

    # Tập trung vào phần toolbar thật (data-is-fake-main-panel="false")
    Wait Until Page Contains Element    css:iframe[id^="tradingview_"]    10s
    Select Frame    css:iframe[id^="tradingview_"]

    # Các selector ưu tiên cho nút Indicators trong toolbar thật
    ${indicator_selectors}=    Create List
    ...    css:#header-toolbar-indicators button[data-name="open-indicators-dialog"]
    ...    xpath=//div[@id="header-toolbar-indicators"]/button[@data-name="open-indicators-dialog"]
    ...    xpath=//div[@id="header-toolbar-indicators"]/button[.//div[text()='Indicators']]
    ...    css:button[data-name="open-indicators-dialog"][aria-label*="Indicators"]
    ...    xpath=//button[@data-name="open-indicators-dialog" and contains(@aria-label, 'Indicators')]

    ${indicator_found}=    Set Variable    ${False}
    
    FOR    ${selector}    IN    @{indicator_selectors}
        Log    Đang thử selector: ${selector}    level=WARN
        
        ${found}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${selector}    5s
        IF    ${found}
            ${element_count}=    Get Element Count    ${selector}
            Log    Tìm thấy ${element_count} element với selector: ${selector}   level=WARN
            
            # Scroll và highlight element để debug
            Scroll Element Into View    ${selector}
            ${element}=    Get WebElement    ${selector}
            Execute JavaScript    arguments[0].style.border='3px solid red';    ARGUMENTS    ${element}
            Sleep    1s
            
            # Lấy thông tin chi tiết về element
            ${element_info}=    Get Element Attribute    ${selector}    outerHTML
            Log    Element info: ${element_info}   level=WARN
            
            # Thử click bằng JavaScript trước
            ${click_success}=    Run Keyword And Return Status    Execute JavaScript    arguments[0].click();    ARGUMENTS    ${selector}
            IF    ${click_success}
                Log    ✅ Click bằng JavaScript thành công   level=WARN
            ELSE
                # Thử click thông thường
                ${click_success}=    Run Keyword And Return Status    Click Element    ${selector}
                IF    ${click_success}
                    Log    ✅ Click thông thường thành công   level=WARN
                ELSE
                    Log    ❌ Cả hai cách click đều thất bại   level=WARN
                    Continue For Loop
                END
            END
            
            Sleep    3s
            
            # Kiểm tra xem dialog indicators có mở không
            ${dialog_visible}=    Run Keyword And Return Status    Wait Until Page Contains Element    css:.dialog-[data-name='indicator-dialog'], [data-name*='indicator'], .dialog--indicators    5s
            IF    ${dialog_visible}
                Log    ✅ Dialog indicators đã mở thành công    level=WARN
                
                # Thực hiện chọn indicators nếu có
                Run Keyword If    '${indicators}' != '[]'    Select Indicators Dialog
                ${indicator_found}=    Set Variable    ${True}
                BREAK
            ELSE
                Log    ❌ Dialog indicators không mở, thử lại với selector khác    level=WARN
                Continue For Loop
            END
        ELSE
            Log    Không tìm thấy element với selector: ${selector}   level=WARN
        END
    END

    IF    not ${indicator_found}
        Log    ⚠️ KHÔNG THỂ TÌM THẤY NÚT INDICATORS - CẦN DEBUG CHI TIẾT    level=WARN
        
        # Debug: tìm tất cả các phần tử trong header-toolbar-indicators
        ${indicator_container}=    Run Keyword And Return Status    Wait Until Page Contains Element    css:#header-toolbar-indicators    5s
        IF    ${indicator_container}
            ${container_html}=    Get Element Attribute    css:#header-toolbar-indicators    outerHTML
            Log    Container HTML: ${container_html}    level=WARN
            
            # Tìm tất cả button trong container
            ${buttons}=    Get WebElements    css:#header-toolbar-indicators button
            FOR    ${button}    IN    @{buttons}
                ${button_text}=    Get Text    ${button}
                ${button_aria}=    Get Element Attribute    ${button}    aria-label
                ${button_data}=    Get Element Attribute    ${button}    data-name
                ${button_class}=    Get Element Attribute    ${button}    class
                Log    Button trong container - Text: ${button_text} | Aria: ${button_aria} | Data-name: ${button_data} | Class: ${button_class}    level=WARN
            END
        ELSE
            Log    Không tìm thấy container #header-toolbar-indicators    level=WARN
        END
        
        # Chụp ảnh toàn trang và HTML để debug
        Capture Page Screenshot    screenshots/debug_indicators_not_found.png
        
        # Lấy toàn bộ HTML của toolbar để kiểm tra
        ${toolbar_html}=    Get Element Attribute    css:.toolbar-qqNP9X6e    outerHTML
        Create File    screenshots/toolbar_debug.html    ${toolbar_html}
        
        Fail    KHÔNG THỂ TÌM VÀ CLICK VÀO NÚT INDICATORS
    END

Select Indicators Dialog
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


Select Indicators
    # Parse indicators từ JSON string thành list
    ${parsed_indicators}=    Evaluate    json.loads('''${indicators}''')    json
    
    FOR    ${indicator}    IN    @{parsed_indicators}
        ${indicator_clean}=    Strip String    ${indicator}
        Log    Đang chọn indicator: ${indicator_clean}
        
        # Thử nhiều selector khác nhau cho indicator
        ${indicator_selectors}=    Create List
        ...    xpath=//div[contains(text(), "${indicator_clean}")]
        ...    xpath=//span[contains(text(), "${indicator_clean}")]
        ...    xpath=//button[contains(text(), "${indicator_clean}")]
        ...    xpath=//div[contains(@class, 'item') and contains(text(), "${indicator_clean}")]
        
        ${indicator_found}=    Set Variable    ${False}
        FOR    ${selector}    IN    @{indicator_selectors}
            ${found}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${selector}    3s
            IF    ${found}
                Log    Tìm thấy indicator với selector: ${selector} level=WARN
                Click Element    ${selector}
                ${indicator_found}=    Set Variable    ${True}
                Sleep    1s
                BREAK
            END
        END
        
        IF    not ${indicator_found}
            Log    Không thể tìm thấy indicator "${indicator_clean}"    level=WARN
        END
    END