from troposphere import Parameter


def add_parameters(template, dic):

    for parameter in dic['parameters']:
        template.add_parameter(Parameter(
            parameter,
            **dic['parameters'][parameter]
        ))

    return template
