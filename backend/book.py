class Book:
    def __init__(self, title, author, first_publish_year, subjects, description):
        self.title = title
        self.author = author
        self.first_publish_year = first_publish_year
        self.subjects = subjects
        self.description = description

    def display(self):
        print("\n=== Book Information ===")
        print(f"Title: {self.title}")
        print(f"Author: {self.author}")
        print(f"First Published: {self.first_publish_year}")

        print("\nSubjects:")
        for subject in self.subjects:
            print(f"- {subject}")

        print("\nDescription:")
        print(self.description)

    def get_profile(self):
        return f"""
        Subjects:
        {", ".join(self.subjects)}

        Description:
        {self.description}
        """

    @classmethod
    def from_openlibrary_result(cls, search_result, work_details):
        author = search_result.get("author_name", ["Unknown"])[0]
        first_publish_year = search_result.get("first_publish_year", "Unknown")

        subjects = work_details.get("subjects", [])[:20]

        description = work_details.get("description", "")
        if isinstance(description, dict):
            description = description.get("value", "")

        # Open Library sometimes concatenates multiple language versions of the
        # same description, separated by a blank line. Keep only the first
        # block so embeddings aren't diluted by duplicate content in another language.
        description = description.split("\r\n\r\n")[0].split("\n\n")[0].strip()

        if not description or len(subjects) < 2:
            return None

        return cls(
            title=search_result.get("title", "Unknown"),
            author=author,
            first_publish_year=first_publish_year,
            subjects=subjects,
            description=description
        )