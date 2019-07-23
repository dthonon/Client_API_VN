 A new field is added to src_vn.observers to anonymize observers: 
 pseudo_observer_uid. It should be used for data exchance to respect
 user privacy. It is encoded by HMAC, using db_secret_key token.
