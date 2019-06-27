UUID are not (re)created during columns tables creation.
For observations, they are in a separate uui_xref table. They can be
obtained by joining observations and uui_xref on (site=site and id=id_sighing)

They are dropped for other tables.