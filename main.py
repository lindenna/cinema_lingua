from flask import Flask, render_template, request, redirect, url_for

import os
from dotenv import load_dotenv

import requests

load_dotenv()
TOKEN = os.getenv("TOKEN")

app = Flask(__name__)


@app.route("/")
def index():
    if "error" in request.args:
        return render_template("index.html", error=request.args["error"])
    return render_template("index.html")


@app.route("/info", methods=["GET", "POST"])
def info():
    if request.method == "GET":
        # Get page number from query params, default to 1
        page = request.args.get("page", default=1, type=int)
        country = request.args.get("country")
        language = request.args.get("language")
        provider = request.args.get("provider")
    else:
        form_data = request.form
        country = form_data["country"]
        language = form_data["language"]
        provider = form_data["provider"]
        page = 1

    headers = {"accept": "application/json", "Authorization": f"Bearer {TOKEN}"}

    countries_url = "https://api.themoviedb.org/3/configuration/countries"
    countries = requests.get(countries_url, headers=headers).json()
    country_item = next(
        (
            item
            for item in countries
            if item["english_name"].lower() == country.lower()
            or item["native_name"].lower() == country.lower()
        ),
        None,
    )

    if not country_item:
        return redirect(url_for("index", error="Country not found"))
    country_name = country_item["iso_3166_1"]

    languages_url = "https://api.themoviedb.org/3/configuration/languages"
    languages = requests.get(languages_url, headers=headers).json()
    language_item = next(
        (
            item
            for item in languages
            if item["english_name"].lower() == language.lower()
        ),
        None,
    )

    if not language_item:
        return redirect(url_for("index", error="Language not found"))
    language_name = language_item["iso_639_1"]

    if provider:
        providers_url = "https://api.themoviedb.org/3/watch/providers/movie"
        providers = requests.get(providers_url, headers=headers).json()
        provider_item = next(
            (
                item
                for item in providers["results"]
                if item["provider_name"].lower() == provider.lower()
            ),
            None,
        )

        if not provider_item:
            return redirect(url_for("index", error="Provider not found"))

        provider_id = provider_item["provider_id"]

    genres_url = "https://api.themoviedb.org/3/genre/movie/list"
    genres = requests.get(genres_url, headers=headers).json()
    selected_genres = request.form.getlist("genres")
    for genre in selected_genres:
        genre_item = next(
            (item for item in genres["genres"] if item["name"].lower() == genre), None
        )
        if genre_item:
            genre_id = genre_item["id"]
            if "with_genres" in locals():
                with_genres += f",{genre_id}"
            else:
                with_genres = str(genre_id)

    if not provider and "with_genres" not in locals():
        url = f"https://api.themoviedb.org/3/discover/movie?with_origin_country={country_name}&with_original_language={language_name}&page={page}"
    elif not provider and "with_genres" in locals():
        url = f"https://api.themoviedb.org/3/discover/movie?with_origin_country={country_name}&with_original_language={language_name}&with_genres={with_genres}&page={page}"
    elif provider and "with_genres" not in locals():
        url = f"https://api.themoviedb.org/3/discover/movie?with_origin_country={country_name}&with_original_language={language_name}&with_watch_providers={provider_id}&watch_region=US&page={page}"
    elif provider and "with_genres" in locals():
        url = f"https://api.themoviedb.org/3/discover/movie?with_origin_country={country_name}&with_original_language={language_name}&with_watch_providers={provider_id}&watch_region=US&with_genres={with_genres}&page={page}"

    movie_data = requests.get(url, headers=headers).json()

    poster_paths = []
    titles = []
    release_dates = []
    overviews = []

    for movie in movie_data["results"]:

        if movie["poster_path"] is None:
            poster_paths.append(None)
        else:
            poster_paths.append(
                "https://image.tmdb.org/t/p/w500" + movie["poster_path"]
            )

        title = movie["title"]
        titles.append(title)

        release_date = movie["release_date"]
        date_items = release_date.split("-")
        if len(date_items) == 3:
            release_date = f"{date_items[1]}/{date_items[2]}/{date_items[0]}"
        release_dates.append(release_date)

        overview = movie["overview"]
        overviews.append(overview)

    total_pages = movie_data.get("total_pages", 1)

    return render_template(
        "info.html",
        titles=titles,
        release_dates=release_dates,
        overviews=overviews,
        poster_paths=poster_paths,
        info={
            "country": country.capitalize(),
            "language": language.capitalize(),
            "genres": selected_genres,
            "provider": provider.capitalize() if provider else None,
            "page": page,
            "total_pages": total_pages,
        },
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500, debug=True)
