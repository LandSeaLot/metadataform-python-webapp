from copy import deepcopy


def generate_txt(parsed_metadata, columns):
    parsed_metadata = deepcopy(parsed_metadata)
    lines = []

    global_attributes = parsed_metadata.get(
        "global_attributes",
        {},
    )

    # creators fix
    if "creators" in global_attributes:
        creators = global_attributes["creators"]

        creator_names = []
        creator_orcids = []
        creator_roles = []

        for creator in creators:

            if creator.get("name"):
                creator_names.append(creator["name"])
                creator_orcid = creator.get("orcid", "")
                if creator_orcid is None:
                    creator_orcid = ""
                creator_orcids.append(creator_orcid)
                creator_roles.append(creator.get("role", ""))

        global_attributes["creator_name"] = ";".join(creator_names)

        global_attributes["creator_orcid"] = ";".join([c for c in creator_orcids])

        global_attributes["creator_role"] = ";".join(creator_roles)

        del global_attributes["creators"]

    # contributors fix
    if "contributors" in global_attributes:
        contributors = global_attributes["contributors"]

        contributor_names = []
        contributor_orcids = []
        contributor_roles = []

        for contributor in contributors:

            if contributor.get("name"):
                contributor_names.append(contributor["name"])
                contributor_orcid = contributor.get("orcid", "")
                if contributor_orcid is None:
                    contributor_orcid = ""
                contributor_orcids.append(contributor_orcid)
                contributor_roles.append(contributor.get("role", ""))

        global_attributes["contributors_name"] = ";".join(contributor_names)

        global_attributes["contributors_orcid"] = ";".join(contributor_orcids)

        global_attributes["contributors_role"] = ";".join(contributor_roles)

        del global_attributes["contributors"]

    # description fix:
    if "summary" in global_attributes:
        global_attributes["description"] = (
            global_attributes["summary"]
            .replace(
                "LandSeaLot has received funding from the European Union’s Horizon Europe Framework Programme for Research and Innovation under grant agreement No 101134575. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or European Research Executive Agency. Neither the European Union nor the granting authority can be held responsible for them. UK participantsin Horizon Europe Project LandSeaLot are supportedby UKRI grant numbers: 10109592 University of Stirling and 10107554 Plymouth Marine Laboratory.",
                "",
            )
            .replace("This dataset is part of the LandSeaLot project outcomes.", "")
        )

    lines.append("Global attributes:")

    # cleaning and sorting
    global_attributes = {
        k: v
        for k, v in global_attributes.items()
        if v and v != "null" and k not in ["sensor_id", "summary"]
    }
    sorted_global_attributes = dict(
        sorted(global_attributes.items(), key=lambda item: item[0])
    )
    flattened_attrs = {}

    for key, value in sorted_global_attributes.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for sub_key, sub_value in value.items():
                if not sub_value:
                    continue
                lines.append(f"    {sub_key}: {sub_value}")
                flattened_attrs[sub_key] = sub_value

        elif isinstance(value, list):
            lines.append(f"{key}:")
            if key not in flattened_attrs:
                flattened_attrs[key] = []

            for item in value:
                if not value:
                    continue

                lines.append(f"    {item}")
                flattened_attrs[key].append(item)

        else:
            if isinstance(value, str):
                value = value.replace("<br>", "")
            lines.append(f"{key}: {value}")
            flattened_attrs[key] = value

    variables = parsed_metadata.get(
        "variables",
        {},
    )

    vars_in_df = {v: vd for v, vd in variables.items() if vd.get("code", "") in columns}
    if vars_in_df:
        lines.append("")
        lines.append("Variables:")

        for variable_name, variable in vars_in_df.items():

            lines.append("")
            lines.append(f"{variable_name}:")

            for key, value in variable.items():
                lines.append(f"    {key}: {value}")

    return "\n".join(lines), flattened_attrs


def save_txt(parsed_metadata, output_path, columns):
    content, flattened_attrs = generate_txt(parsed_metadata, columns)

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:
        f.write(content)

    return flattened_attrs
