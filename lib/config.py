def GetSection(all_config, section):
    section = section.upper()
    if section in all_config.sections():
        return all_config[section]
    return {}
