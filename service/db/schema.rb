# This file is auto-generated from the current state of the database. Instead of editing this file, 
# please use the migrations feature of Active Record to incrementally modify your database, and
# then regenerate this schema definition.
#
# Note that this schema.rb definition is the authoritative source for your database schema. If you need
# to create the application database on another system, you should be using db:schema:load, not running
# all the migrations from scratch. The latter is a flawed and unsustainable approach (the more migrations
# you'll amass, the slower it'll run and the greater likelihood for issues).
#
# It's strongly recommended to check this file into your version control system.

ActiveRecord::Schema.define(:version => 20090303190609) do

  create_table "extensions", :force => true do |t|
    t.string   "mid"
    t.string   "name"
    t.string   "icon_url"
    t.string   "updateRDF"
    t.text     "description"
    t.text     "creator"
    t.string   "homepageURL"
    t.text     "developers"
    t.text     "translators"
    t.text     "contributors"
    t.datetime "created_at"
    t.datetime "updated_at"
  end

  create_table "profile_extensions", :force => true do |t|
    t.integer  "extension_id"
    t.integer  "profile_id"
    t.string   "version"
    t.datetime "created_at"
    t.datetime "updated_at"
  end

  create_table "profiles", :force => true do |t|
    t.integer  "user_id"
    t.string   "name"
    t.string   "secret"
    t.string   "os"
    t.string   "version"
    t.string   "platform"
    t.datetime "created_at"
    t.datetime "updated_at"
  end

  create_table "users", :force => true do |t|
    t.string   "name"
    t.datetime "created_at"
    t.datetime "updated_at"
  end

end
