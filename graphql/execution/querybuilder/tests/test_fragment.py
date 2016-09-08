# '''
# {
#     books {
#         title
#         author {
#             name
#         }
#     }
# }'''
# BooksFragment(
# 	('title', str(resolve_title())),
# 	('author', AuthorFragment(
# 		('name', str(resolve_author()))
# 	))
# )