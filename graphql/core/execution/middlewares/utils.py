def tag_resolver(f, tag):
    """
    Tags a resolver function with a specific tag that can be read by a Middleware to denote specific functionality.
    :param f: The function to tag.
    :param tag: The tag to add to the function.
    :return: The function with the tag added.
    """
    if not hasattr(f, '_resolver_tags'):
        f._resolver_tags = set()

    f._resolver_tags.add(tag)
    return f


def resolver_has_tag(f, tag):
    """
        Checks to see if a function has a specific tag.
    """
    if not hasattr(f, '_resolver_tags'):
        return False

    return tag in f._resolver_tags


def merge_resolver_tags(source_resolver, target_resolver):
    if not hasattr(source_resolver, '_resolver_tags'):
        return target_resolver

    if not hasattr(target_resolver, '_resolver_tags'):
        target_resolver._resolver_tags = set()

    target_resolver._resolver_tags |= source_resolver._resolver_tags
    return target_resolver
