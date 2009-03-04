# Be sure to restart your server when you modify this file.

# Your secret key for verifying cookie session data integrity.
# If you change this key, all old sessions will become invalid!
# Make sure the secret is at least 30 characters and all random, 
# no regular words or you'll be exposed to dictionary attacks.
ActionController::Base.session = {
  :key         => '_service_session',
  :secret      => '91d4bd07a71e4c4a94eb69caa99067d6d65666b6defeec1da5876f5ec5ade8fe0c1f1a6cbaba809e9001912d2cc7833d1801a00a241f2c4722e2394353b50921'
}

# Use the database for sessions instead of the cookie-based default,
# which shouldn't be used to store highly confidential information
# (create the session table with "rake db:sessions:create")
# ActionController::Base.session_store = :active_record_store
