from bs4 import BeautifulSoup
import lxml.etree
import lxml.builder

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
    if xml == "Test Case does not contain steps":
        steps_expected_list = [['\n','\n']]
    else:
        html_list = parse_xml_steps(xml)
        steps_expected_list = []
        for html_step in html_list:
            clean_step_expected_list = [
                action for action in html_step
            ]
            steps_expected_list.append(clean_step_expected_list)
    return steps_expected_list


def convert_to_xml(test_case):
    E = lxml.builder.ElementMaker()
    xml_steps = E.steps
    xml_step = E.step
    xml_action = E.parameterizedString
    xml_expected_result = E.parameterizedString
    xml_description = E.description
    xml_doc = xml_steps(id="0", last=str(len(test_case)+1)
    )

    for test_case_step in test_case:
        step_number = str(test_case_step[0]+1)
        step_action = test_case_step[1]
        step_expected_result = test_case_step[2]

        out = xml_step(
            xml_action(step_action, isformatted="true"),
            xml_expected_result(step_expected_result, isformatted="true"),
            xml_description(),
            id=step_number, type="ActionStep",
        )
        xml_doc.append(out)
    result_steps_xml = (str(lxml.etree.tostring(xml_doc))[2:-1])
    # print(result_steps_xml.replace('"', '\\"'))
    return result_steps_xml