# Listing from Section 8.13 of the textbook “Fundamentals of Business Process Analysis and Modelling in IT”.

Scenario: Attempt to publish a piece without legal review
  Given the piece is flagged as having legal risks
  And the lawyer has not yet marked it "reviewed"
  When the release editor clicks "Publish"
  Then the system refuses publication with the message "Lawyer review required"
  And the publication attempt is recorded in the audit log

Scenario: Publication after review
  Given the piece is flagged as having legal risks
  And the lawyer has marked the current version of the text "reviewed"
  When the release editor clicks "Publish"
  Then the piece is published
