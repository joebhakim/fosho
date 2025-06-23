# Downstream, we want to have something like:

```


# Warn here if not validated
wrapped_df = fosho.read_csv(file="data/static_notes.csv", 
                            schema="data_and_schemas/static_notes.yaml", 
                            validation_artifacts="static_notes_validation_artifacts")


wrapped_df.validate() # Error here if not validated

print(wrapped_df['a'] ) # This data is as trustworthy as the validator


```


# When you have just the data (static_notes.csv)

Step 1: Generate the schema guess:

`...`

Step 2: Human-check the schema guess


`Open the yml file in your favorite text editor. Read it with your human eyes.`

Step 3a: the schema is wrong (passes pandera validation but missing something crucial)

`Edit the yml to fix it manually.`

Step 3b: the schema is wrong (does not pass pandera validation)

`Note to dev: this shouldn't happen eventually? For now, Edit the yml to fix it manually.`

Step 3c: the schema is correct (does all the validations you need from it). Sign it!

`...`

This produces the validation artifacts that get invalidated when the data or schema changes. Now, 
the above `wrapped_df.validate()` will pass.

...

