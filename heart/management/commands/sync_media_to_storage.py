from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Copie les fichiers présents dans MEDIA_ROOT vers le stockage Django par défaut (ex. Cloudflare R2)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Réécrit les objets déjà présents dans le stockage distant.",
        )

    def handle(self, *args, **options):
        if not getattr(settings, "USE_CLOUDFLARE_R2", False):
            raise CommandError(
                "Activez USE_CLOUDFLARE_R2=True avant de synchroniser les médias vers R2."
            )

        source_root = Path(settings.MEDIA_ROOT)
        if not source_root.exists():
            raise CommandError(f"MEDIA_ROOT introuvable : {source_root}")

        files = [path for path in source_root.rglob("*") if path.is_file()]
        if not files:
            self.stdout.write(self.style.WARNING("Aucun fichier média local à synchroniser."))
            return

        uploaded = 0
        skipped = 0
        for path in files:
            relative_name = path.relative_to(source_root).as_posix()
            exists = default_storage.exists(relative_name)
            if exists and not options["force"]:
                skipped += 1
                continue
            if exists:
                default_storage.delete(relative_name)
            with path.open("rb") as source:
                default_storage.save(relative_name, File(source, name=path.name))
            uploaded += 1
            self.stdout.write(f"✓ {relative_name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Synchronisation terminée : {uploaded} envoyé(s), {skipped} ignoré(s)."
            )
        )
