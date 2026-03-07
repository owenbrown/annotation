from babel.numbers import list_currencies
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.utils.translation import gettext_lazy as _

from core.models import TimestampedModel
from core.veryfi_mysql import TransactionsMLDocument


class Annotator(TimestampedModel):
    name = models.CharField(max_length=255, null=False)
    email = models.EmailField(null=False, unique=True)
    accuracy_google_drive_folder_id = models.CharField(max_length=255, null=True)
    clockify_email = models.EmailField(null=True, unique=True)


class AnnotationFormat(models.TextChoices):
    COCO = "COCO 1.0", "COCO 1.0"
    PICKLIST_LABELEDCHECK = "Picklist Labeled Check 1.0", "Picklist Labeled Check 1.0"


class Platform(models.TextChoices):
    CVAT_REMOTE = "CVAT_REMOTE", _("CVAT Remote")
    CVAT_LOCAL = "CVAT_LOCAL", _("CVAT Local")
    GOOGLE_FORM = "GOOGLE_FORM", _("Google Form")
    SAPIEN_S3 = "SAPIEN_S3", _("Sapien S3")


class AnnotationTask(TimestampedModel):
    adjudication = models.BooleanField(default=False)
    annotations = models.JSONField(null=True)
    annotations_format = models.CharField(
        max_length=255, choices=AnnotationFormat.choices, null=True
    )
    annotator = models.ForeignKey(
        Annotator, on_delete=models.PROTECT, related_name="annotation_tasks"
    )
    name = models.CharField(max_length=255, null=False)
    description = models.TextField(null=True)
    images = models.ManyToManyField("MLDocumentImage", related_name="images")
    review_of_submission = models.ForeignKey(
        "AnnotationSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="review_tasks",
    )

    platform = models.CharField(max_length=20, choices=Platform.choices, null=True, blank=True)
    platform_task_id = models.IntegerField(null=True, blank=True)
    schema_file_name = models.CharField(max_length=50, null=True)

    class Meta:
        unique_together = ("annotator", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "platform_task_id"], name="unique_platform_platform_task_id"
            )
        ]

    def clean(self):
        # Check if one field is null while the other is not
        if (self.platform is None) != (self.platform_task_id is None):
            raise ValidationError(
                _(
                    "Both platform and platform_task_id must be either provided together or left empty."
                )
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class AnnotationJob(TimestampedModel):
    task = models.ForeignKey("AnnotationTask", on_delete=models.PROTECT, related_name="jobs")
    platform = models.CharField(max_length=20, choices=Platform.choices, null=False, blank=False)
    platform_job_id = models.IntegerField(null=True)
    annotation_annotator = models.ForeignKey(
        Annotator, on_delete=models.PROTECT, related_name="annotation_jobs", null=True
    )
    validation_annotator = models.ForeignKey(
        Annotator, on_delete=models.PROTECT, related_name="validation_jobs", null=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["platform", "platform_job_id"], name="unique_platform_platform_job_id"
            )
        ]


class AnnotationSubmission(TimestampedModel):
    annotator = models.ForeignKey(
        Annotator, on_delete=models.PROTECT, related_name="annotation_submissions"
    )
    task = models.ForeignKey(
        "AnnotationTask", on_delete=models.PROTECT, related_name="submissions", null=True
    )
    data = models.JSONField(null=False)
    data_format = models.CharField(max_length=255, null=False)
    google_form_response_id = models.CharField(max_length=255, null=True)
    job = models.ForeignKey(
        "AnnotationJob", on_delete=models.PROTECT, related_name="submissions", null=True
    )
    submitted_at = models.DateTimeField(null=False)
    source_s3_bucket = models.TextField(null=True)
    source_s3_path = models.TextField(null=True)
    trusted = models.BooleanField(null=True, default=False)
    platform = models.CharField(max_length=20, choices=Platform.choices, null=True, blank=True)
    platform_task_id = models.IntegerField(null=True, blank=True)
    raw_data = models.JSONField(null=True)

    class Meta:
        unique_together = ("source_s3_bucket", "source_s3_path")


class MLDocument(TimestampedModel):
    """Each ML Document maps 1-on-1 with a row in the MySQL manhattan_2.transactions_mldocument table."""

    document_type = models.CharField(max_length=255, null=False)
    mldocument_id = models.IntegerField(null=False, unique=True)
    unique_check_fields = models.JSONField(null=False)
    excluded_for_test = models.BooleanField(default=False)

    # Called by multple scripts, so it is here
    @staticmethod
    def get_unique_fields(d: TransactionsMLDocument) -> dict:
        """Create a dict that is used for uniqueness checks.

        Args:
            d: dict: This is the "TransactionsMLDocument", which is
                a row from MySQL manhattan_2.transactions_mldocument
                after json.load() on "ml_responses"
        """
        fields = {}
        for k in [
            "check_number",
            "payer_name",
            "check_account_routing",
            "bank_name",
            "receiver_name",
        ]:
            try:
                ml_responses = d["ml_responses"]
                extract_check = ml_responses["extract_check"]
                result = extract_check["result"]
                this_field_result = result[k]

                v = "||".join(str(v["value"]) for v in this_field_result)
                fields[k] = v
            except KeyError:
                fields[k] = None
        return fields


class MLDocumentImage(TimestampedModel):
    # Order and s3_path URL come from
    # manhattan_2.transactions_mldocument, field ml_responses["pp_result"]["extracted_images"]
    mldocument = models.ForeignKey(
        MLDocument, on_delete=models.CASCADE, null=True, related_name="images"
    )
    transactions_receipt_id = models.IntegerField(null=True, blank=True)
    order = models.IntegerField(null=False)

    # When original is True, it's the original, un-deskewed, un-cropped image.
    original = models.BooleanField(null=False)

    # this is the image that matches the pb.gz file.
    ocred_image_path = models.URLField(null=True, blank=True)

    # this is the image we annotated. It might be rotated.
    s3_path = models.URLField(null=True, unique=True)

    @property
    def image_url(self):
        return f"https://cdn.veryfi.com/{self.s3_path}"

    @property
    def ocred_image_url(self):
        return f"https://cdn.veryfi.com/{self.ocred_image_path}" if self.ocred_image_path else None

    class Meta:
        unique_together = [
            ("order", "mldocument", "transactions_receipt_id", "original"),
            ("original", "ocred_image_path"),
        ]

    def save(self, *args, **kwargs):
        # Condition 1: if original is True, s3_path must contain "_original"
        if self.original and (self.s3_path is not None) and "_original" not in self.s3_path:
            raise ValueError('If "original" is True, "s3_path" must contain "_original".')

        super().save(*args, **kwargs)


class MLDocumentImageAnnotation(TimestampedModel):
    class CheckType(models.TextChoices):
        BACK_OF_CHECK = "back_of_check", "Back of Check"
        # BANK_DRAFT is depricated and will be removed.
        BANK_DRAFT = "bank_draft", "Bank Draft"
        BILL_PAY_DRAFT = "bill_pay_draft", "Bill Pay Draft"
        BUSINESS_CHECK = "business_check", "Business Check"
        CASHIERS_CHECK = "cashiers_check", "Cashier's Check"
        CERTIFIED_CHECK = "certified_check", "Certified Check"
        GOVERNMENT_CHECK = "government_check", "Government Check"
        MONEY_ORDER = "money_order", "Money Order"
        PERSONAL_CHECK = "personal_check", "Personal Check"
        TELLER_CHECK = "teller_check", "Teller Check"
        STARTER_CHECK = "starter_check", "Starter Check"
        # Unknown is depricated and willl be removed.
        UNKNOWN = "unknown", "Unknown"

    class DocumentValidity(models.TextChoices):
        GOOD = "good", "Good"
        BAD_DOC_NOT_CHECK = "bad_doc_not_check", "Bad Document - Not a check"
        BAD_DOC_MULTIPLE = "bad_doc_multiple", "Bad Document - Multiple checks"
        BAD_DOC_OTHER = "bad_doc_other", "Bad Document - Other"
        DUPLICATE = "duplicate", "Duplicate"

    class Status(models.TextChoices):
        COMPLETE = "complete", "Complete"
        COMPLETE_WITH_ISSUES = "complete_with_issues", "Complete with Issues"
        IN_PROGRESS = "in_progress", "In Progress"
        BAD_DOC_NOT_CHECK = "bad_doc_not_check", "Bad Document - Not a check"
        BAD_DOC_MULTIPLE = "bad_doc_multiple", "Bad Document - Multiple checks"
        BAD_DOC_OTHER = "bad_doc_other", "Bad Document - Other"
        DUPLICATE = "duplicate", "Duplicate"
        NOT_STARTED = "not_started", "Not Started"

    adjudicated = models.BooleanField(default=False)
    annotator = models.ForeignKey(
        Annotator, on_delete=models.PROTECT, null=False, related_name="ml_document_annotations"
    )
    check_type = models.CharField(choices=CheckType.choices, max_length=50, null=True, blank=True)
    currency = models.CharField(max_length=3, null=True, blank=True)
    document_validity = models.CharField(
        choices=DocumentValidity.choices, max_length=50, null=False, blank=False
    )
    issues = models.TextField(blank=True, null=True)
    golden = models.BooleanField(default=False)
    mldocument_image = models.ForeignKey(
        MLDocumentImage, on_delete=models.PROTECT, null=False, related_name="annotations"
    )
    status = models.CharField(choices=Status.choices, max_length=50, null=False)
    submission = models.ForeignKey(
        AnnotationSubmission, on_delete=models.PROTECT, null=False, related_name="annotations"
    )
    job = models.ForeignKey(
        AnnotationJob,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        related_name="mldocument_image_annotations",
    )

    class Meta:
        unique_together = ("submission", "mldocument_image")

    def _validate_golden_status(self):
        """Ensure only one golden annotation exists per document image."""
        if not self.golden:
            return

        existing_golden = MLDocumentImageAnnotation.objects.filter(
            mldocument_image=self.mldocument_image, golden=True
        )

        if self.pk:
            existing_golden = existing_golden.exclude(pk=self.pk)

        if existing_golden.exists():
            from django.core.exceptions import ValidationError

            raise ValidationError("There can only be one golden annotation per document image.")

    def _validate_status_and_issues(self):
        """Update status if complete with issues."""
        if self.status == self.Status.COMPLETE and self.issues:
            self.status = self.Status.COMPLETE_WITH_ISSUES

    def correct_check_type(self):
        if self.check_type == "Back of Check":
            self.check_type = self.CheckType.BACK_OF_CHECK

    def add_document_validity(self):
        """Add document validity if not present."""
        if not self.document_validity:
            Status = self.Status
            DocumentValidity = self.DocumentValidity
            status_to_document_validity = {
                Status.COMPLETE: DocumentValidity.GOOD,
                Status.COMPLETE_WITH_ISSUES: DocumentValidity.GOOD,
                Status.IN_PROGRESS: DocumentValidity.GOOD,
                Status.NOT_STARTED: DocumentValidity.GOOD,
                Status.BAD_DOC_NOT_CHECK: DocumentValidity.BAD_DOC_NOT_CHECK,
                Status.BAD_DOC_MULTIPLE: DocumentValidity.BAD_DOC_MULTIPLE,
                Status.BAD_DOC_OTHER: DocumentValidity.BAD_DOC_OTHER,
                Status.DUPLICATE: DocumentValidity.DUPLICATE,
            }
            status_enum = self.Status(self.status)
            self.document_validity = status_to_document_validity[status_enum]

    def clean(self):
        self.currency = (
            self.currency.upper()
            if self.currency and self.currency.upper() in list_currencies()
            else None
        )
        self._validate_status_and_issues()
        self._validate_golden_status()

    def save(self, *args, **kwargs):
        self.correct_check_type()
        self.add_document_validity()
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_final_annotation_ids(cls):
        """
        Returns the highest-indexed id for each annotator_id, mldocument_image_id permutation.

        The reason is, only want to consider the final value an annotator provided.
        An older workflow allowed the annotator to submit multiple times.
        """

        latest_annotations = MLDocumentImageAnnotation.objects.values(
            "annotator_id", "mldocument_image_id"
        ).annotate(max_id=Max("id"))
        return latest_annotations.values_list("max_id", flat=True)


class PointsField(models.JSONField):
    """The format is [x1, y1, x2, y2, x3, y3, ...]"""

    def __init__(self, *args, coordinate_type="pixel", **kwargs):
        self.coordinate_type = coordinate_type  # "pixel" or "relative"
        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        # First run the parent JSONField validation
        super().validate(value, model_instance)

        if not isinstance(value, list):
            raise ValidationError(f"{self.name} must be a list")

        if len(value) % 2 != 0:
            raise ValidationError(f"{self.name} must have an even number of elements")

        if len(value) < 6:
            raise ValidationError(f"{self.name} must have at least 3 points (6 values)")

        if not all(isinstance(x, (int, float)) for x in value):
            raise ValidationError(f"{self.name} must contain only numbers")

        if self.coordinate_type == "relative":
            if not all(0.0 <= x <= 1.0 for x in value):
                raise ValidationError(f"{self.name} values must be between 0 and 1")

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["coordinate_type"] = self.coordinate_type
        return name, path, args, kwargs


class Polygon(TimestampedModel):
    TYPE_TEXT = "text"
    TYPE_REGION = "region"
    TYPE_DATE = "date"
    TYPE_CHECKBOX = "checkbox"  # New type for checkboxes
    TYPE_CHOICES = [
        (TYPE_TEXT, "Text"),
        (TYPE_REGION, "Region"),
        (TYPE_DATE, "Date"),
        (TYPE_CHECKBOX, "Checkbox"),  # Add to choices
    ]

    polygon_type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=False)
    category = models.CharField(max_length=255, null=False)
    is_checked = models.BooleanField(blank=True, null=True)
    mldocument_image_annotation = models.ForeignKey(
        MLDocumentImageAnnotation, on_delete=models.PROTECT, related_name="polygons"
    )
    points_pixels = PointsField(default=list, null=False, coordinate_type="pixel")  # type: ignore[call-arg]
    points_relative = PointsField(default=list, null=False, coordinate_type="relative")  # type: ignore[call-arg]

    # Only used for text type
    handwriting = models.BooleanField(blank=True, null=True)
    value = models.TextField(blank=True, null=True)

    # Only used for type date
    format = models.CharField(max_length=255, blank=True, null=True)

    def _get_points_relative(self):
        # import here to avoid circular dependency
        from core import image_cache_utils

        image_path = image_cache_utils.get_file_return_path(
            self.mldocument_image_annotation.mldocument_image.image_url
        )
        width, height = image_cache_utils.get_dimensions(image_path)
        abs_points = self.points_pixels
        # iterate over each pair of points and divide by width and height
        rel_points = []
        for i in range(0, len(abs_points), 2):
            rel_points.append(abs_points[i] / width)
            rel_points.append(abs_points[i + 1] / height)
        return rel_points

    def clean(self):
        if self.polygon_type == self.TYPE_REGION:
            if self.handwriting is not None:
                raise ValidationError("Region polygons cannot have handwriting value")
            if self.is_checked is not None:
                raise ValidationError("Region polygons must have null is_checked")

        elif self.polygon_type == self.TYPE_TEXT:
            if self.handwriting is None:
                raise ValidationError("Text polygons must specify handwriting")
            if self.is_checked is not None:
                raise ValidationError("Text polygons must have null is_checked")

        elif self.polygon_type == self.TYPE_CHECKBOX:
            # For checkbox type, value cannot be None and must be either "true" or "false"
            if self.value is not None:
                print(f"during validation the value for a checkbox was {self.value}")
                raise ValidationError(
                    "Checkbox polygons should have value=null. Use is_checked instead"
                )
            if self.is_checked not in [True, False]:
                raise ValidationError(
                    f"Checkbox polygons should have is_checked as True or False, but got {self.is_checked}"
                )

        elif self.polygon_type == self.TYPE_DATE:
            if self.is_checked is not None:
                raise ValidationError("Date polygons must have null is_checked")

        if self.polygon_type != self.TYPE_DATE and self.format:
            raise ValidationError("format is only allowed for date polygons")

        if self.value == "":
            self.value = None

        if self.value:
            self.value = self.value.replace(" \n", "\n")
            self.value = self.value.strip()

    def save(self, *args, **kwargs):
        if isinstance(self.handwriting, str):
            self.handwriting = {"true": True, "false": False, "null": None}[
                self.handwriting.lower()
            ]
        self.points_relative = self._get_points_relative()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Polygon(id={self.id})"


class MLDocumentImageAnnotationPatch(TimestampedModel):
    mldocument = models.ForeignKey(MLDocument, on_delete=models.PROTECT, related_name="delete")
    mldocument_image_annotation = models.ForeignKey(
        MLDocumentImageAnnotation, on_delete=models.PROTECT, related_name="patches"
    )

    annotator = models.ForeignKey(
        Annotator,
        on_delete=models.PROTECT,
        null=False,
        related_name="ml_document_annotation_patches",
    )
    meta_field = models.CharField(max_length=255, null=False)
    old_value = models.CharField(max_length=3, null=True, blank=True)
    new_value = models.CharField(max_length=3, null=True, blank=True)
