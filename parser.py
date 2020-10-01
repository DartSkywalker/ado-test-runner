from bs4 import BeautifulSoup


def parse_xml_steps(xml):
    soup = BeautifulSoup(xml, 'lxml')
    parsed_steps_from_xml = soup.find_all('step')
    # print(parsed_steps_from_xml)
    parsed_html_steps = []
    for xml_step in parsed_steps_from_xml:
        soup_step_expected = BeautifulSoup(str(xml_step), 'lxml')
        parsed_step_expected = soup_step_expected.find_all('parameterizedstring')
        if len(parsed_step_expected) == 2:
            step_action = parsed_step_expected[0].text
            expected_result = parsed_step_expected[1].text
        else:
            step_action = parsed_step_expected[0].text
            expected_result = ""
        parsed_html_steps.append([step_action, expected_result])
    return parsed_html_steps

def parse_html_steps(xml):
    html_list = parse_xml_steps(xml)
    steps_expected_list = []
    for html_step in html_list:
        clean_step_expected_list = [
            action\
            .replace("<BR/>", "\n")\
            .replace("<BR />", "\n")\
            .replace("&gt", "")\
            .replace("</P>", "\n")\
            .replace("<P>", "")\
            .replace("</DIV>", "")\
            .replace("<DIV>", "") for action in html_step
        ]
        steps_expected_list.append(clean_step_expected_list)
    return steps_expected_list