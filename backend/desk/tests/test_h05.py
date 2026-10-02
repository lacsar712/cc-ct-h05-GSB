"""H05 回归：刀号格只放刀号，刀补格只放微米，四面读齐不串列。

覆盖：
- 甲刀 5 微米、乙刀 24 微米：提交响应 / 列表 / 详情 / 数据库 四面读齐；
- 提交失败（空刀号、未登录）不得残留任何行；
- 复核员只读，提交一律 403；
- worker 复核结论：5 合格、24 超差，且结论基于未串列的真实微米值。
"""

import json

from django.test import TestCase
from django.utils import timezone

from desk.auth_utils import create_access_token
from desk.models import OffsetSubmission, User
from desk.services import apply_verdict


def bearer(user):
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(user)}"}


def get_json(client, path, user):
    return client.get(path, **bearer(user))


def post_json(client, path, payload, user=None):
    kwargs = {"content_type": "application/json", "data": json.dumps(payload)}
    if user is not None:
        kwargs.update(bearer(user))
    return client.post(path, **kwargs)


class ColumnAlignmentTests(TestCase):
    """甲刀 5µm / 乙刀 24µm：写入、投影、列表、详情四面一致。"""

    def setUp(self):
        self.machinist = User.objects.create_user(
            username="machinist", password="machine123456", role=User.Role.MACHINIST
        )
        self.auditor = User.objects.create_user(
            username="auditor", password="audit123456", role=User.Role.AUDITOR
        )

    def _assert_columns_aligned(self, payload, row):
        # 刀号格只能是刀号，刀补格只能是微米，绝不能整列对调
        self.assertEqual(row["tool_code"], payload["tool_code"])
        self.assertEqual(row["offset_um"], payload["offset_um"])
        self.assertNotEqual(str(row["offset_um"]), payload["tool_code"])

    def test_create_response_keeps_columns(self):
        for tool, um in (("甲刀01", 5), ("乙刀02", 24)):
            payload = {"tool_code": tool, "offset_um": um}
            resp = post_json(self.client, "/api/submissions", payload, self.machinist)
            self.assertEqual(resp.status_code, 200, resp.content)
            data = resp.json()
            self._assert_columns_aligned(payload, data)
            self.assertEqual(data["status"], OffsetSubmission.Status.PENDING)

    def test_database_row_keeps_columns(self):
        post_json(
            self.client,
            "/api/submissions",
            {"tool_code": "甲刀01", "offset_um": 5},
            self.machinist,
        )
        post_json(
            self.client,
            "/api/submissions",
            {"tool_code": "乙刀02", "offset_um": 24},
            self.machinist,
        )
        rows = list(OffsetSubmission.objects.order_by("id"))
        self.assertEqual([(r.tool_code, r.offset_um) for r in rows],
                         [("甲刀01", 5), ("乙刀02", 24)])

    def test_list_endpoint_reads_aligned(self):
        post_json(
            self.client,
            "/api/submissions",
            {"tool_code": "甲刀01", "offset_um": 5},
            self.machinist,
        )
        post_json(
            self.client,
            "/api/submissions",
            {"tool_code": "乙刀02", "offset_um": 24},
            self.machinist,
        )
        resp = get_json(self.client, "/api/submissions", self.auditor)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        by_tool = {r["tool_code"]: r for r in data}
        self.assertEqual(set(by_tool), {"甲刀01", "乙刀02"})
        self._assert_columns_aligned(
            {"tool_code": "甲刀01", "offset_um": 5}, by_tool["甲刀01"]
        )
        self._assert_columns_aligned(
            {"tool_code": "乙刀02", "offset_um": 24}, by_tool["乙刀02"]
        )

    def test_detail_endpoint_reads_aligned(self):
        create = post_json(
            self.client,
            "/api/submissions",
            {"tool_code": "甲刀01", "offset_um": 5},
            self.machinist,
        ).json()
        resp = get_json(self.client, f"/api/submissions/{create['id']}", self.auditor)
        self.assertEqual(resp.status_code, 200)
        self._assert_columns_aligned(
            {"tool_code": "甲刀01", "offset_um": 5}, resp.json()
        )

    def test_create_and_detail_and_db_all_agree(self):
        payload = {"tool_code": "乙刀02", "offset_um": 24}
        created = post_json(
            self.client, "/api/submissions", payload, self.machinist
        ).json()
        detail = get_json(
            self.client, f"/api/submissions/{created['id']}", self.auditor
        ).json()
        listing = get_json(self.client, "/api/submissions", self.auditor).json()
        db_row = OffsetSubmission.objects.get(pk=created["id"])
        for view in (created, detail, listing[0]):
            self.assertEqual(view["tool_code"], "乙刀02")
            self.assertEqual(view["offset_um"], 24)
        self.assertEqual(db_row.tool_code, "乙刀02")
        self.assertEqual(db_row.offset_um, 24)


class FailurePathTests(TestCase):
    """提交失败不得残留错位脏行。"""

    def setUp(self):
        self.machinist = User.objects.create_user(
            username="machinist", password="machine123456", role=User.Role.MACHINIST
        )

    def test_blank_tool_code_leaves_no_row(self):
        before = OffsetSubmission.objects.count()
        resp = post_json(
            self.client,
            "/api/submissions",
            {"tool_code": "   ", "offset_um": 5},
            self.machinist,
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(OffsetSubmission.objects.count(), before)

    def test_anonymous_post_leaves_no_row(self):
        resp = post_json(
            self.client,
            "/api/submissions",
            {"tool_code": "甲刀01", "offset_um": 5},
            user=None,
        )
        self.assertIn(resp.status_code, (401, 403))
        self.assertEqual(OffsetSubmission.objects.count(), 0)


class AuditorReadOnlyTests(TestCase):
    """复核侧仍不可写。"""

    def setUp(self):
        self.auditor = User.objects.create_user(
            username="auditor", password="audit123456", role=User.Role.AUDITOR
        )

    def test_auditor_cannot_submit_and_no_row_is_created(self):
        before = OffsetSubmission.objects.count()
        resp = post_json(
            self.client,
            "/api/submissions",
            {"tool_code": "甲刀01", "offset_um": 5},
            self.auditor,
        )
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(OffsetSubmission.objects.count(), before)

    def test_auditor_can_read_list_and_detail(self):
        machinist = User.objects.create_user(
            username="machinist", password="machine123456", role=User.Role.MACHINIST
        )
        created = post_json(
            self.client,
            "/api/submissions",
            {"tool_code": "甲刀01", "offset_um": 5},
            machinist,
        ).json()
        self.assertEqual(
            get_json(self.client, "/api/submissions", self.auditor).status_code, 200
        )
        self.assertEqual(
            get_json(
                self.client, f"/api/submissions/{created['id']}", self.auditor
            ).status_code,
            200,
        )


class VerdictTests(TestCase):
    """结论必须基于未串列的真实微米值：5 合格、24 超差。"""

    def setUp(self):
        self.machinist = User.objects.create_user(
            username="machinist", password="machine123456", role=User.Role.MACHINIST
        )

    def _run_verdict(self, tool, um):
        row = OffsetSubmission.objects.create(
            tool_code=tool,
            offset_um=um,
            submitted_by=self.machinist,
            status=OffsetSubmission.Status.PENDING,
        )
        apply_verdict(row)
        row.refresh_from_db()
        return row

    def test_five_microns_passes_twentyfour_fails(self):
        jia = self._run_verdict("甲刀01", 5)
        yi = self._run_verdict("乙刀02", 24)
        self.assertEqual(jia.verdict, OffsetSubmission.Verdict.PASS)
        self.assertEqual(yi.verdict, OffsetSubmission.Verdict.FAIL)
        self.assertEqual(jia.status, OffsetSubmission.Status.DONE)
        self.assertEqual(yi.status, OffsetSubmission.Status.DONE)
        self.assertIsNotNone(jia.reviewed_at)
        self.assertLessEqual(
            abs((timezone.now() - yi.reviewed_at).total_seconds()), 300
        )
        # 复核不改动刀号/刀补两列
        self.assertEqual((jia.tool_code, jia.offset_um), ("甲刀01", 5))
        self.assertEqual((yi.tool_code, yi.offset_um), ("乙刀02", 24))
