import argparse
import bs4
from bs4 import BeautifulSoup
import re

def read_html(file_path: str) -> str:
    """Read and return the contents of a .HTML file.
    
    Parameters:
        file_path - A string representing the path to the desired .HTML file.
    
    Returns:
        A string of the text representation of the provided .HTML file. In the event of a FileNotFoundError error, returns None.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return None
        
def write_java_file(class_name: str, text_content: str) -> None:
    """Writes a text file as <class_name>.java with the provided text_content.
    
    Parameters:
        class_name - A string with the name of the class for the file that is being written. class_name also determines the name of the file. ex: If class_name = "MyClass", the created file's name will be "MyClass.java".
        text_content - A string with the contents of the text file. This should be valid java code.
        
    Returns:
        None
    """
    with open(class_name + '.java', 'w+', encoding="utf-8") as file:
        file.write(text_content)

def clean_characters(string: str) -> str:
    """Replaces all non-breaking spaces with normal spaces.
    
    Parameters:
        string - A string that might have non-breaking spaces to be replaced.
    
    Returns:
        A string with non-breaking spaces replaced with normal spaces.
    """
    return string.replace('\u00A0', ' ')

def remove_linebreaks(string: str) -> str:
    """Removes all newline and carriage return characters.
    
    Parameters:
        string - A string that might have linebreaks to be removed.
    
    Returns:
        A string with no linebreaks.
    """
    return string.replace('\n', '').replace('\r', '')

def remove_many_spaces(string: str) -> str:
    """Replaces all instances of 10 or more spaces with only one space. This method is used to fix instances where Eclipse adds many spaces to html tags.
    
    Parameters:
        string - A string that might have long sequences of spaces.
    
    Returns:
        A string without long sequences of spaces.
    """
    return re.sub(r'\s{10,}', ' ', string)

def parse_javadoc_body(parent: bs4.element.Tag) -> str:
    """Parses the main description for a javadoc from a BeautifulSoup tag.
    
    Parameters:
        parent - A bs4.element.Tag CONTAINING a html div with class="block" containing the main description of a javadoc.
        
    Returns:
        A string representing the main description of a javadoc.
    """
    javadoc_body = parent.find('div', class_='block')
    if javadoc_body:
        return remove_linebreaks(javadoc_body.encode_contents().decode('utf-8'))
    else:
        return ''

def parse_field_li(field_li: bs4.element.Tag) -> str:
    """Parses a BeautifulSoup li tag representing one of the class's fields.
    
    Parameters:
        field_li - A bs4.element.Tag of a li of a field from the fields details section.
    
    Returns:
        A string containing the javadoc and declaration of a java field.
    """
    signature_div = field_li.find('div', class_='member-signature')
    field_signature = f"{signature_div.find('span', class_='modifiers').text.strip()} {signature_div.find('span', class_='return-type').text.strip()} {signature_div.find('span', class_='element-name').text.strip()}"

    return f'/**\n * {parse_javadoc_body(field_li)}\n */\n{field_signature};'

def parse_method_notes_dl(notes_dl: bs4.element.Tag) -> tuple:
    """Parses, from a BeautifulSoup dl tag, a method's parameters, what the method throws, what the method returns, and whether the method overrides another method.
    
    Parameters:
        notes_dl - A bs4.element.Tag of a dl from a method's notes section.
        
    Returns:
        A tuple as: (the method's parameters as a list of strings, what the method throws as a list of strings, what the method returns as a string, if the method overrides another method or not as a boolean)
    """
    parameters = []
    throws = []
    returns = ''
    overrides = False

    # find parameters
    parameters_dt = notes_dl.find('dt', string='Parameters:')
    if parameters_dt:
        sibling = parameters_dt.find_next_sibling()
        while sibling and sibling.name == 'dd':
            parameters.append(sibling.text)
            sibling = sibling.find_next_sibling()
    
    # find throws
    throws_dt = notes_dl.find('dt', string='Throws:')
    if throws_dt:
        sibling = throws_dt.find_next_sibling()
        while sibling and sibling.name == 'dd':
            throws.append(sibling.text)
            sibling = sibling.find_next_sibling()
            
    returns_dt = notes_dl.find('dt', string='Returns:')
    if returns_dt:
        returns = returns_dt.find_next_sibling('dd').text
    
    if notes_dl.find('dt', string='Overrides:') == None:
        overrides = False
    else:
        overrides = True
    
    return (parameters, throws, returns, overrides)

def parse_method_li(method_li: bs4.element.Tag) -> str:
    """Parses a BeautifulSoup li tag representing one of the class's methods.
    
    Parameters:
        method_li - A bs4.element.Tag of a li of a method from the methods details section.
    
    Returns:
        A string containing the javadoc and declaration of a java function with a default return statement.
    """
    return_string = ''
    
    # parse html
    signature_div = method_li.find('div', class_='member-signature')
    method_signature = signature_div.find('span', class_='modifiers').text.strip()
    return_type = signature_div.find('span', class_='return-type')

    # build method signature (everything but throws)
    if return_type != None:
        return_type = return_type.text.strip()
        method_signature += ' ' + return_type
    method_signature += ' ' + signature_div.find('span', class_='element-name').text.strip()
    parameters = signature_div.find('span', class_='parameters')
    if parameters != None:
        method_signature += remove_linebreaks(clean_characters(parameters.text.strip()))
    else:
        method_signature += '()'

    # add main part of javadoc to return string
    return_string = f'/**\n * {parse_javadoc_body(method_li)}\n'
    
    # get things needed for javadoc
    javadoc_notes = method_li.find('dl', class_='notes')
    javadoc_parameters, javadoc_throws, javadoc_returns, overrides = [], [], '', False
    if javadoc_notes:
        javadoc_parameters, javadoc_throws, javadoc_returns, overrides = parse_method_notes_dl(javadoc_notes)
    
    # now that we have throws, add it to the method signature
    if javadoc_throws != []: # if the method throws checked exceptions
        method_signature += ' throws '
        for javadoc_throw in javadoc_throws:
            exception_name = re.match(r'^[A-Za-z]+', javadoc_throw)
            if exception_name:
                method_signature += f'{remove_linebreaks(remove_many_spaces(exception_name.group()))}, '
        method_signature = method_signature[:-2] # get rid of last space and comma
    
    # add params to javadoc part of return string
    if javadoc_parameters != []: # if the method has parms
        return_string += ' * \n'
        for javadoc_parameter in javadoc_parameters:
            return_string += f' * @param {remove_linebreaks(remove_many_spaces(javadoc_parameter))}\n'
    
    # add return to javadoc part of return string
    if javadoc_returns != '':
        return_string += f' * \n * @return {remove_linebreaks(remove_many_spaces(javadoc_returns))}\n'
    
    # add throws to javadoc part of return string
    if javadoc_throws != []: # if the method throws checked exceptions
        return_string += ' * \n'
        for javadoc_throw in javadoc_throws:
            return_string += f' * @throws {remove_linebreaks(remove_many_spaces(javadoc_throw))}\n'

    # add @Override if needed
    return_string +=  ' */\n'
    return_string += '@Override\n' if overrides else ''

    # add method declaration and default return statement to return string
    return_string += method_signature + ' {\n    // TODO: Implement\n\n'
    if return_type not in (None, 'void'):
        return_string += '    return '
        if return_type in ('byte', 'int', 'short'):
            return_string += '0'
        elif return_type == 'long':
            return_string += '0L'
        elif return_type == 'float':
            return_string += '0.0f'
        elif return_type == 'double':
            return_string += '0.0d'
        elif return_type == 'char':
            # change this to a printable char?
            return_string += '\u0000'
        elif return_type == 'boolean':
            return_string += 'false'
        else:
            return_string += 'null'
        return_string += '; // default return statement\n'
    return_string += '  }'
    
    
    return return_string

def parse_class(class_soup: bs4.BeautifulSoup) -> str:
    """Parses the javadoc and declaration of the class from the class's BeautifulSoup html.
    
    Parameters:
        class_soup - The class's BeautifulSoup html.
    
    Returns:
        A string containing the javadoc and declaration of the class as valid java code. Note: the returned string does not contain a closing brace for the class.
    """
    class_description_section = class_soup.find('section', class_='class-description')
    
    signature_div = class_description_section.find('div', class_='type-signature')
    class_signature = f"{signature_div.find('span', class_='modifiers').text.strip()} {signature_div.find('span', class_='element-name type-name-label').text.strip()}"
    implements = signature_div.find('span', class_='extends-implements').text.strip()
    if implements != None and 'extends Object' in implements:
        class_signature += ' ' + implements.replace('extends Object', '').strip()

    return f'/**\n * {parse_javadoc_body(class_description_section)}\n */\n{class_signature} {{\n\n'

def parse_fields(class_soup: bs4.BeautifulSoup) -> str:
    """Parses the javadocs and declarations of the fields from the class's BeautifulSoup html. If no fields exist, an empty string is returned.
    
    Parameters:
        class_soup - The class's BeautifulSoup html.
    
    Returns:
        A string containing the javadocs and declarations of the fields as valid java code. If no fields exist, an empty string is returned.
    """
    field_details_section = class_soup.find('section', class_='field-details')
    
    return_string = ''

    if field_details_section != None:
        field_list = field_details_section.find('ul', class_='member-list')
        for li in field_list.find_all('li', recursive=False):
            return_string += parse_field_li(li) + '\n\n'

    return return_string

def parse_constructor(class_soup: bs4.BeautifulSoup) -> str:
    """Parses the javadocs and declarations of the constructors from the class's BeautifulSoup html. If no constructors exist, an empty string is returned.
    
    Parameters:
        class_soup - The class's BeautifulSoup html.
    
    Returns:
        A string containing the javadocs and declarations of the constructors as valid java code. If no constructors exist, an empty string is returned.
    """
    constructor_details_section = class_soup.find('section', class_='constructor-details')
    
    return_string = ''
    
    if constructor_details_section != None:
        field_list = constructor_details_section.find('ul', class_='member-list')
        for li in field_list.find_all('li', recursive=False):
            return_string += parse_method_li(li) + '\n\n'

    return return_string

def parse_methods(class_soup: bs4.BeautifulSoup) -> str:
    """Parses the javadocs and declarations of the methods from the class's BeautifulSoup html. If no methods exist, an empty string is returned.
    
    Parameters:
        class_soup - The class's BeautifulSoup html.
    
    Returns:
        A string containing the javadocs and declarations of the methods as valid java code. If no methods exist, an empty string is returned.
    """
    method_details_section = class_soup.find('section', class_='method-details')
    
    return_string = ''

    if method_details_section != None:
        field_list = method_details_section.find('ul', class_='member-list')
        for li in field_list.find_all('li', recursive=False):
            return_string += parse_method_li(li) + '\n\n'

    return return_string

def parse_soup(class_soup: bs4.BeautifulSoup) -> str:
    """Parses the html from a class's documentation file to valid java code.
    
    Parameters:
        class_soup - The class's BeautifulSoup html.
    
    Returns:
        A string of the declaration of the class with its fields, constuctors, and methods declared, all with javadocs.
    """
    class_string = parse_class(class_soup)
    fields_string = parse_fields(class_soup)
    constructor_string = parse_constructor(class_soup)
    methods_string = parse_methods(class_soup)
    
    return class_string + fields_string + constructor_string + methods_string + '}'


def main():
    parser = argparse.ArgumentParser(description="Convert an Java class .html file generated by Eclipse to a .java source file.")
    parser.add_argument("file", type=str, help="The path to the .html file to convert.")
    args = parser.parse_args()

    html = read_html(args.file)
    
    if html == None:
        print("File doesn't exist")
        quit()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    content = parse_soup(soup)
    
    class_name = soup.find('span', class_='element-name type-name-label').text
    
    write_java_file(class_name, content)

if __name__ == "__main__":
    main()