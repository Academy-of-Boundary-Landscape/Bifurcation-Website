from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException

from app.api.v1.auth import exchange_sso_login, read_users_me, update_user_me
from app.models.user import User, UserRole
from app.schemas.sso import SSOExchangeRequest
from app.schemas.user import UserUpdate
from app.services import sso
from app.services.sso import _create_state_token

from tests.test_support import BackendAsyncTestCase, ExecuteResult, mock_request as _mock_request


class TestSSOExchange(BackendAsyncTestCase):
    async def test_exchange_sso_code_creates_admin_user_from_claims(self) -> None:
        claims = {
            "sub": "casdoor-sub-001",
            "email": "admin@example.com",
            "preferred_username": "admin_seed",
            "name": "Admin Seed",
            "roles": ["admin"],
        }

        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                ExecuteResult(first=None),
                ExecuteResult(all_items=[]),
                ExecuteResult(first=None),
            ]
        )
        db.add = Mock()
        db.commit = AsyncMock()

        async def refresh_side_effect(user: User) -> None:
            user.id = 101

        db.refresh = AsyncMock(side_effect=refresh_side_effect)

        with (
            patch.object(sso.settings, "SSO_ADMIN_CLAIM_KEYS", "roles,role,groups"),
            patch.object(sso.settings, "SSO_ADMIN_MATCH_VALUES", "admin,administrator"),
            patch.object(sso, "_exchange_code_for_tokens", AsyncMock(return_value={"id_token": "fake"})),
            patch.object(sso, "_resolve_claims", AsyncMock(return_value=claims)),
        ):
            result = await sso.exchange_sso_code(
                db,
                code="fake-code",
                state=_create_state_token("/books/42"),
            )

        user = result["user"]
        self.assertTrue(result["is_new_user"])
        self.assertEqual(result["redirect_to"], "/books/42")
        self.assertEqual(user.id, 101)
        self.assertEqual(user.auth_provider, "casdoor")
        self.assertEqual(user.auth_subject, "casdoor-sub-001")
        self.assertEqual(user.role, UserRole.ADMIN)
        self.assertEqual(user.email, "admin@example.com")

    async def test_exchange_sso_code_keeps_banned_role_on_sync(self) -> None:
        banned_user = User(
            id=11,
            email="banned@example.com",
            username="banned_writer",
            role=UserRole.BANNED,
            is_active=True,
            hashed_password="",
            auth_provider="casdoor",
            auth_subject="casdoor-sub-banned",
        )

        claims = {
            "sub": "casdoor-sub-banned",
            "email": "banned@example.com",
            "preferred_username": "banned_writer",
            "roles": ["admin"],
        }

        db = AsyncMock()
        db.execute = AsyncMock(side_effect=[ExecuteResult(first=banned_user)])
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        with (
            patch.object(sso.settings, "SSO_ADMIN_CLAIM_KEYS", "roles"),
            patch.object(sso.settings, "SSO_ADMIN_MATCH_VALUES", "admin"),
            patch.object(sso, "_exchange_code_for_tokens", AsyncMock(return_value={"id_token": "fake"})),
            patch.object(sso, "_resolve_claims", AsyncMock(return_value=claims)),
        ):
            result = await sso.exchange_sso_code(
                db,
                code="fake-code",
                state=_create_state_token("/books"),
            )

        self.assertFalse(result["is_new_user"])
        self.assertEqual(result["user"].id, banned_user.id)
        self.assertEqual(result["user"].role, UserRole.BANNED)

    async def test_exchange_sso_code_rejects_ambiguous_email_auto_link(self) -> None:
        claims = {
            "sub": "casdoor-sub-ambiguous",
            "email": "same@example.com",
            "preferred_username": "same_user",
        }

        existing_1 = User(
            id=1,
            email="same@example.com",
            username="same_1",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )
        existing_2 = User(
            id=2,
            email="same@example.com",
            username="same_2",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )

        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                ExecuteResult(first=None),
                ExecuteResult(all_items=[existing_1, existing_2]),
            ]
        )

        with (
            patch.object(sso, "_exchange_code_for_tokens", AsyncMock(return_value={"id_token": "fake"})),
            patch.object(sso, "_resolve_claims", AsyncMock(return_value=claims)),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await sso.exchange_sso_code(
                    db,
                    code="fake-code",
                    state=_create_state_token("/books"),
                )

        self.assertEqual(ctx.exception.status_code, 409)

    async def test_auth_exchange_endpoint_returns_local_access_token(self) -> None:
        user = User(
            id=7,
            email="writer@example.com",
            username="writer_user",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
        )

        with patch(
            "app.api.v1.auth.exchange_sso_code",
            AsyncMock(
                return_value={
                    "user": user,
                    "is_new_user": False,
                    "redirect_to": "/books",
                }
            ),
        ):
            response = await exchange_sso_login(
                _mock_request(),
                SSOExchangeRequest(code="fake-code", state="fake-state"),
                db=AsyncMock(),
            )

        self.assertEqual(response.token_type, "bearer")
        self.assertEqual(response.redirect_to, "/books")
        self.assertFalse(response.is_new_user)
        self.assertTrue(response.access_token)

    async def test_read_users_me_returns_profile_with_counts(self) -> None:
        now = datetime.now(timezone.utc)
        current_user = User(
            id=12,
            email="me@example.com",
            username="me_user",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
            created_at=now,
            updated_at=now,
            bio="bio",
            avatar="https://example.com/avatar.png",
        )

        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[
                ExecuteResult(scalar=5),
                ExecuteResult(scalar=9),
            ]
        )

        profile = await read_users_me(current_user=current_user, db=db)

        self.assertEqual(profile.id, current_user.id)
        self.assertEqual(profile.nodes_count, 5)
        self.assertEqual(profile.likes_count, 9)
        self.assertEqual(profile.username, "me_user")
        self.assertEqual(profile.created_at, now)
        self.assertEqual(profile.updated_at, now)

    async def test_update_user_me_applies_profile_changes(self) -> None:
        now = datetime.now(timezone.utc)
        current_user = User(
            id=13,
            email="update@example.com",
            username="before_name",
            role=UserRole.WRITER,
            is_active=True,
            hashed_password="",
            created_at=now,
            updated_at=now,
            bio="old bio",
            avatar=None,
        )

        db = AsyncMock()
        db.add = Mock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        result = await update_user_me(
            user_update=UserUpdate(
                username="after_name",
                bio="new bio",
                avatar="https://example.com/new.png",
            ),
            current_user=current_user,
            db=db,
        )

        self.assertEqual(result.username, "after_name")
        self.assertEqual(result.bio, "new bio")
        self.assertEqual(result.avatar, "https://example.com/new.png")
        db.add.assert_called_once_with(current_user)
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once_with(current_user)
