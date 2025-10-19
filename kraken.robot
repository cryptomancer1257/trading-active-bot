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

# Selectors linh hoạt - tìm bằng multiple attributes
${HEADER_TIMEFRAME_CONTAINER}    css:div[data-testid="time-intervals-container"], div#header-toolbar-intervals, div[class*="intervals"]
${HEADER_TIMEFRAME_BUTTONS}      css:div#header-toolbar-intervals button, div[data-testid="time-intervals-container"] button

# Selectors cho dropdown menu
${DROPDOWN_MENU_CONTAINER}       css:div[class*="menuWrap"], div[class*="menu-container"], div[class*="menu-"]
${DROPDOWN_MENU_ITEMS}           css:div[class*="item-"], div[role="menuitem"]


# Selectors cho fullscreen
${FULLSCREEN_BUTTON}             xpath=//button[contains(@aria-label, 'Maximize')]

*** Tasks ***
ScreenShot Image not login
    ${parsed_timeframes}=    Evaluate    json.loads('''${timeframe}''')    json
    Set Global Variable    ${parsed_timeframes}
    Log    Danh sách timeframe cần xử lý: ${parsed_timeframes}    level=WARN

    ${kraken_pair}=    Replace String    ${trading_pair}    _    -
    ${url}=    Set Variable    https://pro.kraken.com/app/trade/${kraken_pair}
    ${options}=    Evaluate    {'arguments': ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--window-size=1920,1080', '--force-device-scale-factor=1']}

    TRY
        Open Available Browser    ${url}    browser_selection=chrome    options=${options}
        Log    Đã mở browser thành công: ${url}    level=WARN
    EXCEPT    AS    ${error}
        Log    Failed to open browser: ${error}    level=ERROR
        Fail    Browser initialization failed
    END

    Sleep    8s  # Tăng thời gian chờ
    Handle Cookie Popup
    Sleep    3s
    Click Fullscreen Kraken
    Load And Select Indicators
    Sleep    3s
    
    FOR    ${tf}    IN    @{parsed_timeframes}
        Log    ====== Bắt đầu xử lý timeframe: ${tf} ======    level=WARN
        TRY
            Select Timeframe From Dropdown Robust
            Select Timeframe Robust    ${tf}
            Sleep    4s
            
            # Verify chart container hiển thị
            ${chart_visible}=    Run Keyword And Return Status    Wait Until Page Contains Element    css:div[data-testid="chart-container"]    10s
            IF    not ${chart_visible}
                Log    Cảnh báo: Chart container không hiển thị sau khi chọn timeframe ${tf}    level=WARN
            END
            
            ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
            ${filepath}=    Set Variable    screenshots/kraken_${trading_pair}_${tf}_${timestamp}.png
            Capture Page Screenshot    ${filepath}
            Append To File    screenshots/${session_id}_image.txt    ${filepath}\n
            Log    Đã chụp screenshot cho timeframe ${tf}: ${filepath}    level=WARN
        EXCEPT    AS    ${error}
            Log    Lỗi khi xử lý timeframe ${tf}: ${error}    level=ERROR
            ${timestamp}=    Get Current Date    result_format=%Y%m%d_%H%M%S
            ${error_filepath}=    Set Variable    screenshots/error_${trading_pair}_${tf}_${timestamp}.png
            Capture Page Screenshot    ${error_filepath}
            Log    Đã chụp screenshot lỗi: ${error_filepath}    level=ERROR
            Continue For Loop
        END
        Log    ====== Hoàn thành xử lý timeframe: ${tf} ======    level=WARN
    END

*** Keywords ***
Handle Cookie Popup
    Log    Đang xử lý cookie popup...    level=WARN
    Run Keyword And Ignore Error    Wait Until Page Contains Element    //button[contains(., 'Accept')]    5s
    Run Keyword And Ignore Error    Click Button    //button[contains(., 'Accept')]
    Run Keyword And Ignore Error    Wait Until Page Contains Element    //button[contains(., 'AGREE')]    3s
    Run Keyword And Ignore Error    Click Button    //button[contains(., 'AGREE')]
    Log    Đã xử lý cookie popup    level=WARN

Click Fullscreen Kraken
    Log    Đang click nút fullscreen...    level=WARN
    Create Directory    screenshots
    
    ${fullscreen_selectors}=    Create List
    ...    xpath=//button[contains(@aria-label, 'Maximize')]
    ...    xpath=//button[contains(@class, 'maximize')]
    ...    xpath=//button[contains(@title, 'Maximize')]
    ...    xpath=//button[.//*[contains(text(), 'Maximize')]]
    
    ${found}=    Set Variable    ${False}
    FOR    ${selector}    IN    @{fullscreen_selectors}
        ${found}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${selector}    5s
        IF    ${found}
            Scroll Element Into View    ${selector}
            Click Element    ${selector}
            Log    Đã click fullscreen với selector: ${selector}    level=WARN
            BREAK
        END
    END
    
    IF    not ${found}
        Log    Không thể tìm thấy nút fullscreen, tiếp tục mà không fullscreen    level=WARN
        Capture Page Screenshot    screenshots/debug_no_fullscreen.png
    END
    
    Sleep    2s

Load And Select Indicators
    Log    Đang xử lý indicators...    level=WARN
    
    Wait Until Page Contains Element    css:iframe[id^="tradingview_"]    10s
    Select Frame    css:iframe[id^="tradingview_"]

    # Thử nhiều selector khác nhau cho nút Indicators
    ${indicator_selectors}=    Create List
    ...    css:div.apply-common-tooltip[data-tooltip*="Indicators"]
    ...    css:div[data-tooltip*="Indicators"]
    ...    xpath=//div[contains(@data-tooltip, 'Indicators')]
    ...    xpath=//div[normalize-space(.)[contains(., 'Indicators')]]
    ...    xpath=//div[.//span[contains(normalize-space(.), 'Indicators')]]
    ...    xpath=//div[contains(@class,'apply-common-tooltip') and contains(@data-tooltip,'Indicators')]
    ...    xpath=//button[contains(@data-tooltip, 'Indicator')]    # giữ cho an toàn nếu có button khác

    
    ${found}=    Set Variable    ${False}
    FOR    ${selector}    IN    @{indicator_selectors}
        ${found}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${selector}    5s
        IF    ${found}
            Log    Tìm thấy nút Indicators với selector: ${selector}    level=WARN
            Scroll Element Into View    ${selector}
            Click Element    ${selector}
            Log    Đã mở menu Indicators thành công    level=WARN
            BREAK
        END
    END
    
    IF    not ${found}
        Log    Không thể tìm thấy nút Indicators với bất kỳ selector nào    level=WARN
        Capture Page Screenshot    screenshots/debug_no_indicators.png
        RETURN
    END
    
    Sleep    3s
    
    # Chỉ chọn indicators nếu có config
    ${has_indicators}=    Evaluate    len($indicators) > 0
    IF    ${has_indicators}
        Select Indicators
        Log    Đã chọn indicators: ${indicators}    level=WARN
    ELSE
        Log    Không có indicators nào được config, bỏ qua    level=WARN
    END
    
    Sleep    2s
    Log    Đã hoàn thành xử lý indicators    level=WARN

Select Indicators
    ${parsed_indicators}=    Evaluate    json.loads('''${indicators}''')    json,
    
    Log    Đang chọn các indicators: ${parsed_indicators}    level=WARN 
    
    FOR    ${indicator}    IN    @{parsed_indicators}
        ${indicator_clean}=    Strip String    ${indicator}
        Log    Đang chọn indicator: ${indicator_clean}    level=WARN
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

Select Timeframe Robust
    [Arguments]    ${timeframe}
    Log    Đang chọn timeframe: ${timeframe} với phương pháp robust    level=WARN
    
    # Phương pháp 3: Thử click trực tiếp bằng JavaScript
    ${selected}=    Select Timeframe By JavaScript    ${timeframe}
    IF    ${selected}
        Log    Đã chọn timeframe ${timeframe} bằng JavaScript    level=WARN
        Sleep    1s
        Close Timeframe Dropdown
        RETURN
    END
    
    Log    Không thể chọn timeframe ${timeframe} với bất kỳ phương pháp nào    level=ERROR
    Fail    Không thể chọn timeframe ${timeframe}

Select Timeframe From Dropdown Robust
    # Mở dropdown
    ${dropdown_opened}=    Open Timeframe Dropdown Robust
    IF    not ${dropdown_opened}
        Log    Không thể mở dropdown timeframe    level=ERROR
        RETURN    ${False}
    END

*** Keywords ***
Unselect Frame If Active
    TRY
        Unselect Frame
        Log    Đã trở về main frame
    EXCEPT
        Log    Đã ở main frame
    END

Open Timeframe Dropdown Robust
    Log    Đang mở dropdown timeframe với phương pháp robust...    level=WARN
    
    # ĐẢM BẢO CHÚNG TA ĐANG Ở TRONG IFRAME TRADINGVIEW
    Unselect Frame If Active
    Wait Until Page Contains Element    css:iframe[id^="tradingview_"]    30s
    Select Frame    css:iframe[id^="tradingview_"]
    
    # Kiểm tra nếu dropdown đã mở
    ${is_open}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${DROPDOWN_MENU_CONTAINER}    2s
    IF    ${is_open}
        Log    Dropdown timeframe đã mở sẵn    level=WARN
        RETURN    ${True}
    END
    
    # TÌM VÀ XỬ LÝ BUTTON ĐÃ ĐƯỢC XÁC ĐỊNH TỪ TRƯỚC
    Log    Tìm button dropdown bằng phương pháp trực tiếp...    level=WARN
    
    # Phương pháp 1: Tìm tất cả button có class và lọc ra cái visible
    ${all_buttons}=    Get WebElements    xpath=//button[contains(@class, 'menu-S_1OCXUK') and contains(@class, 'button-merBkM5y')]
    ${count}=    Get Length    ${all_buttons}
    Log    Tìm thấy ${count} button với class menu-S_1OCXUK và button-merBkM5y    level=WARN
    
    ${target_button}=    Set Variable    ${None}
    FOR    ${index}    IN RANGE    0    ${count}
        ${btn}=    Get From List    ${all_buttons}    ${index}
        ${is_visible}=    Run Keyword And Return Status    Element Should Be Visible    ${btn}
        ${is_enabled}=    Run Keyword And Return Status    Element Should Be Enabled    ${btn}
        Log    Button ${index + 1}: Visible=${is_visible}, Enabled=${is_enabled}    level=WARN
        
        IF    ${is_visible} and ${is_enabled}
            ${target_button}=    Set Variable    ${btn}
            Log    ✅ Đã tìm thấy button có thể tương tác tại index ${index}    level=WARN
            # Highlight button
            Execute JavaScript    arguments[0].style.border='5px solid red'; arguments[0].style.backgroundColor='orange';    ARGUMENTS    ${target_button}
            BREAK
        END
    END
    
    IF    $target_button is None
        Log    ❌ Không tìm thấy button nào visible và enabled    level=ERROR
        RETURN    ${False}
    END
    
    # THỬ CLICK BẰNG NHIỀU PHƯƠNG PHÁP
    Log    Bắt đầu thử click button dropdown...    level=WARN
    
    # Đảm bảo button trong viewport
    Execute JavaScript    arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});    ARGUMENTS    ${target_button}
    Sleep    2s
    
    # Phương pháp 1: JavaScript click trực tiếp
    TRY
        Execute JavaScript    arguments[0].click();    ARGUMENTS    ${target_button}
        Log    ✅ Đã thử click bằng JavaScript    level=WARN
        Sleep    2s
        
        ${is_open}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${DROPDOWN_MENU_CONTAINER}    3s
        IF    ${is_open}
            Log    ✅ Đã mở dropdown timeframe thành công bằng JavaScript click    level=WARN
            RETURN    ${True}
        END
    EXCEPT
        Log    JavaScript click thất bại    level=WARN
    END
    
    # Phương pháp 2: Selenium click với wait
    TRY
        Wait Until Element Is Visible    ${target_button}    5s
        Click Element    ${target_button}
        Log    ✅ Đã thử click bằng Selenium    level=WARN
        Sleep    2s
        
        ${is_open}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${DROPDOWN_MENU_CONTAINER}    3s
        IF    ${is_open}
            Log    ✅ Đã mở dropdown timeframe thành công bằng Selenium click    level=WARN
            RETURN    ${True}
        END
    EXCEPT
        Log    Selenium click thất bại    level=WARN
    END
    
    # Phương pháp 3: Action Chains - Di chuyển chuột và click
    TRY
        Mouse Over    ${target_button}
        Sleep    1s
        Click Element At Coordinates    ${target_button}    15    15
        Log    ✅ Đã thử click bằng Action Chains    level=WARN
        Sleep    2s
        
        ${is_open}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${DROPDOWN_MENU_CONTAINER}    3s
        IF    ${is_open}
            Log    ✅ Đã mở dropdown timeframe thành công bằng Action Chains    level=WARN
            RETURN    ${True}
        END
    EXCEPT
        Log    Action Chains click thất bại    level=WARN
    END
    
    # Phương pháp 4: JavaScript event dispatch chi tiết
    TRY
        Execute JavaScript    
        ...    var element = arguments[0];
        ...    var rect = element.getBoundingClientRect();
        ...    var x = rect.left + rect.width / 2;
        ...    var y = rect.top + rect.height / 2;
        ...    
        ...    // Tạo và dispatch mouse events
        ...    var mouseDown = new MouseEvent('mousedown', {
        ...        view: window,
        ...        bubbles: true,
        ...        cancelable: true,
        ...        clientX: x,
        ...        clientY: y
        ...    });
        ...    var mouseUp = new MouseEvent('mouseup', {
        ...        view: window,
        ...        bubbles: true,
        ...        cancelable: true,
        ...        clientX: x,
        ...        clientY: y
        ...    });
        ...    var clickEvent = new MouseEvent('click', {
        ...        view: window,
        ...        bubbles: true,
        ...        cancelable: true,
        ...        clientX: x,
        ...        clientY: y
        ...    });
        ...    
        ...    element.dispatchEvent(mouseDown);
        ...    element.dispatchEvent(mouseUp);
        ...    element.dispatchEvent(clickEvent);
        ...    ARGUMENTS    ${target_button}
        
        Log    ✅ Đã thử click bằng JavaScript events chi tiết    level=WARN
        Sleep    2s
        
        ${is_open}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${DROPDOWN_MENU_CONTAINER}    3s
        IF    ${is_open}
            Log    ✅ Đã mở dropdown timeframe thành công bằng JavaScript events    level=WARN
            RETURN    ${True}
        END
    EXCEPT
        Log    JavaScript events click thất bại    level=WARN
    END
    
    # Phương pháp 5: Thử phím Enter
    TRY
        Execute JavaScript    arguments[0].focus();    ARGUMENTS    ${target_button}
        Press Keys    ${target_button}    ENTER
        Log    ✅ Đã thử phím Enter    level=WARN
        Sleep    2s
        
        ${is_open}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${DROPDOWN_MENU_CONTAINER}    3s
        IF    ${is_open}
            Log    ✅ Đã mở dropdown timeframe thành công bằng phím Enter    level=WARN
            RETURN    ${True}
        END
    EXCEPT
        Log    Phím Enter thất bại    level=WARN
    END
    
    # Phương pháp 6: Thử double click
    TRY
        Double Click Element    ${target_button}
        Log    ✅ Đã thử double click    level=WARN
        Sleep    2s
        
        ${is_open}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${DROPDOWN_MENU_CONTAINER}    3s
        IF    ${is_open}
            Log    ✅ Đã mở dropdown timeframe thành công bằng double click    level=WARN
            RETURN    ${True}
        END
    EXCEPT
        Log    Double click thất bại    level=WARN
    END
    
    Log    ❌ Tất cả phương pháp click đều thất bại    level=ERROR
    Capture Page Screenshot    screenshots/debug_all_click_methods_failed.png
    RETURN    ${False}

Select Dropdown Item Robust
    [Arguments]    ${label}
    Log    Đang chọn dropdown item: ${label}    level=WARN

    # Ánh xạ label -> data-value từ HTML thực tế
    &{value_map}=    Create Dictionary
    ...    1 minute=1
    ...    3 minutes=3
    ...    5 minutes=5
    ...    15 minutes=15
    ...    30 minutes=30
    ...    1 hour=60
    ...    2 hours=120
    ...    4 hours=240
    ...    6 hours=360
    ...    12 hours=720
    ...    1 day=1D
    ...    3 days=3D
    ...    1 week=1W
    ...    1 month=1M

    ${target_value}=    Set Variable If
    ...    '${label}' in ${value_map}    ${value_map['${label}']}
    ...    '${label}' not in ${value_map}    ${label}

    Log    Tìm data-value tương ứng của '${label}' là '${target_value}'    level=WARN

    # Thử tìm bằng data-value trước (ổn định hơn text)
    ${selector_by_value}=    Set Variable    xpath=//div[@data-role='menuitem' and @data-value='${target_value}']

    ${found}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${selector_by_value}    5s
    IF    ${found}
        Log    ✅ Tìm thấy item bằng data-value=${target_value}    level=WARN
        Scroll Element Into View    ${selector_by_value}
        Click Element    ${selector_by_value}
        Sleep    2s
        RETURN    ${True}
    END

    # Nếu không có data-value, fallback tìm theo text hiển thị
    ${selector_by_text}=    Set Variable    xpath=//div[@data-role='menuitem']//span[contains(normalize-space(.), '${label}')]
    ${found_text}=    Run Keyword And Return Status    Wait Until Element Is Visible    ${selector_by_text}    5s
    IF    ${found_text}
        Log    ⚠️ Fallback: Tìm thấy item bằng text '${label}'    level=WARN
        Scroll Element Into View    ${selector_by_text}
        Click Element    ${selector_by_text}
        Sleep    2s
        RETURN    ${True}
    END

    Log    ❌ Không tìm thấy dropdown item: ${label} (data-value=${target_value})    level=ERROR
    Capture Page Screenshot    screenshots/debug_item_not_found_${label}.png
    RETURN    ${False}


Select Timeframe By JavaScript
    [Arguments]    ${timeframe}
    Log    Thử chọn timeframe ${timeframe} bằng JavaScript...    level=WARN
    
    &{js_value_map}=    Create Dictionary
    ...    1m=1    5m=5    15m=15    1h=60    4h=240    1D=1D
    ...    1H=60   2H=120  6H=360    12H=720  3D=3D    1W=1W    1M=1M
    
    ${js_value}=    Set Variable If
    ...    '${timeframe}' in ${js_value_map}    ${js_value_map['${timeframe}']}
    ...    '${timeframe}' not in ${js_value_map}    ${timeframe}
    
    ${success}=    Run Keyword And Return Status    Execute JavaScript
    ...    var buttons = document.querySelectorAll('button[data-value="${js_value}"]');
    ...    if (buttons.length > 0) { buttons[0].click(); return true; }
    ...    
    ...    var divs = document.querySelectorAll('div');
    ...    for (var i = 0; i < divs.length; i++) {
    ...        if (divs[i].textContent && divs[i].textContent.trim() === '${timeframe}') {
    ...            var button = divs[i].closest('button');
    ...            if (button) { button.click(); return true; }
    ...        }
    ...    }
    ...    return false;
    
    IF    ${success}
        Log    Đã chọn timeframe ${timeframe} bằng JavaScript    level=WARN
        Sleep    2s
        RETURN    ${True}
    END
    
    RETURN    ${False}

Close Timeframe Dropdown
    Log    Đang đóng dropdown timeframe...    level=WARN
    TRY
        # Quay về main frame rồi vào lại iframe
        Unselect Frame If Active
        Wait Until Page Contains Element    css:iframe[id^="tradingview_"]    30s
        Select Frame    css:iframe[id^="tradingview_"]

        # Tìm nút dropdown (dùng lại logic trong Open Timeframe Dropdown Robust)
        ${dropdown_buttons}=    Get WebElements    xpath=//button[contains(@class, 'menu-S_1OCXUK') and contains(@class, 'button-merBkM5y')]
        FOR    ${btn}    IN    @{dropdown_buttons}
            ${visible}=    Run Keyword And Return Status    Element Should Be Visible    ${btn}
            ${enabled}=    Run Keyword And Return Status    Element Should Be Enabled    ${btn}
            IF    ${visible} and ${enabled}
                Execute JavaScript    arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});    ARGUMENTS    ${btn}
                Sleep    0.5s
                Execute JavaScript    arguments[0].click();    ARGUMENTS    ${btn}
                Log    ✅ Đã click lại dropdown để đóng menu    level=WARN
                Sleep    1s
                BREAK
            END
        END
    EXCEPT
        Log    ❌ Không thể đóng dropdown timeframe    level=WARN
    END